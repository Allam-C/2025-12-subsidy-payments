import os
import pandas as pd
import pdfplumber
import json
import argparse
from pathlib import Path
from logger_setup import get_logger
from schema_utils import get_table_schema, get_column_names, get_file_validation, get_property_name_configuration
from pdf_utils import find_table_header_index, find_table_end_index, extract_table_lines, validate_file, parse_line, validate_date
from org_property_lookup import get_org_by_short_code, get_property_by_alias

    # pending
    # enhance logging with more details
    # modify input dir based on new Dropbox folder structure
    # handle exceptions more gracefully
    # unit tests for pdfreader functions

CONFIG_FILE = Path(__file__).parent / "config.json"
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)
LOG_PATH = config.get("logs", {}).get("file_path")
LOG_FILE = config.get("logs", {}).get("file_name")
DEFAULT_INPUT_SCHEMA = Path(__file__).parent / "schemas/input.json"
DEFAULT_OUTPUT_SCHEMA = Path(__file__).parent / "schemas/output.json"
INPUT_BASE_DIR = config.get("pipelines", {}).get("input",{}).get("base")
INPUT_TEMPLATE = config.get("pipelines", {}).get("input",{}).get("template")
OUTPUT_DIR = config.get("pipelines", {}).get("staging",{})
ORGS_DATA_FILE = Path(__file__).parent / "org_property_map.json"
with open(ORGS_DATA_FILE, "r") as f:
    orgs_data = json.load(f)

logger = get_logger(log_path=LOG_PATH, base_log_name=LOG_FILE, name="pdfreader_logger")

def find_pdf_list(target_path):
    target_path_dir = Path(target_path)
    if not target_path_dir.exists():
        raise FileNotFoundError(f"The specified path does not exist: {target_path}")
    if not target_path_dir.is_dir():
        raise NotADirectoryError(f"The specified path is not a directory: {target_path}")
    pdf_files = list(target_path_dir.rglob("*.pdf"))
    return pdf_files


def get_property_alias(lines, property_info):
    row_index = property_info.get("row")
    prev_marker = property_info.get("previous_col")
    next_marker = property_info.get("post_col")
    line = lines[row_index-1]
    start_index = line.find(prev_marker)
    end_index = line.find(next_marker)
    if start_index == -1 or end_index == -1:
        raise ValueError("Could not find property name markers in the specified line.")
    raw_segment = line[start_index + len(prev_marker):end_index].split()
    return " ".join(raw_segment)

def parse_input_pdf(pdf_file, timeframe, schema, file_id, table_id=None):
    all_rows = []
    table_schema = get_table_schema(schema, file_id, table_id)
    col_names = get_column_names(schema,file_id,table_id)
    with pdfplumber.open(pdf_file) as pdf:
        for i, page in enumerate(pdf.pages):
            lines = page.extract_text().splitlines()
            if not validate_file(lines, get_file_validation(schema, file_id)):
                raise Exception("PDF validation failed.")
            if not validate_date(lines, get_file_validation(schema, file_id), timeframe):
                raise Exception("PDF does not match the specified timeframe.")
            if i == 0:
                property_alias = get_property_alias(lines, get_property_name_configuration(schema, file_id))
            logger.debug(f"Reading page: {i+1}")
            header_index = int(find_table_header_index(lines, table_schema.get("header_keywords", [])))
            if header_index is None:
                raise Exception("Could not find table header.")
            start_index = header_index + 1
            end_index = int(find_table_end_index(lines, start_index))
            table_lines = extract_table_lines(lines, start_index, end_index)
            parsed_rows = [parse_line(line, table_schema) for line in table_lines]
            all_rows.extend(parsed_rows)
    df = pd.DataFrame(all_rows, columns=col_names)
    return {
        "dataframe": df,
        "property_alias": property_alias
    }

def resolve_property_data(orgs_data, organization, property_alias):
    org = get_org_by_short_code(orgs_data, organization)
    property = get_property_by_alias(org, property_alias)
    return {
        "organization": {
            "id": org.get("id"),
            "name": org.get("name"),
            "short_name": org.get("short_name")
        },
        "property": property
    }

def generate_output_df(df_input, schema, file_id, table_id, params):
    table_schema = get_table_schema(schema, file_id, table_id)
    output_data = {}
    for col in table_schema["columns"]:
        source = col.get("source", "input")
        output_name = col.get("output_name", col["name"])
        if source == "input":
            output_data[output_name] = df_input[col["name"]]
        elif source == "parameter":
            param_name = col.get("name")
            if param_name not in params:
                raise ValueError(f"Parameter {param_name} not provided in parameters.")
            output_data[output_name] = params[param_name]
        elif source == "constant":
            output_data[output_name] = col.get("value")
        else:
            raise ValueError(f"Unknown source type: {source}")
    return pd.DataFrame(output_data)

def main():
    parser = argparse.ArgumentParser(description="Validate Initial Arguments.")
    parser.add_argument("-o","--org", required=True,help="Organization Short Name")
    parser.add_argument("-t","--timeframe",required=True,help="Period in format YYYYMM")
    args = parser.parse_args()
    organization, timeframe = args.org, args.timeframe
    INPUT_DIR = INPUT_TEMPLATE.format(base=INPUT_BASE_DIR, orgId=organization, function="affordable-rd")

    logger.info("********PDF processing started********")
    logger.info("Input Parameters:")
    logger.info(f"Organization: {organization}, Timeframe: {timeframe}")
    logger.info(f"Input Directory: {INPUT_DIR}")
    logger.info(f"Output Directory: {OUTPUT_DIR}")
    with open(DEFAULT_INPUT_SCHEMA, "r") as f:
        input_schema_data = json.load(f)
    logger.info(f"Searching for pdf files in {INPUT_DIR}")
    pdf_files = find_pdf_list(INPUT_DIR)
    if not pdf_files:
        logger.error("No PDF files found matching the criteria.")
        return
    logger.info(f"Found {len(pdf_files)} PDF files to process.")
    file_count = len(pdf_files)
    error_count = 0
    ok_count = 0
    for i,pdf_file in enumerate(pdf_files):
        logger.info(f"Processing file {i+1}: {pdf_file}")
        # Step 1: Read and parse input PDF
        logger.info(f"Reading and parsing input file")
        try:
            input_return = parse_input_pdf(pdf_file, timeframe, input_schema_data, "rd_project_worksheet","rd_subsidy_payments")
            df_input = input_return["dataframe"]
        except Exception as e:
            error_count += 1
            logger.warning(f"Skipping file {pdf_file}: {e}")
            continue

        # Step 2: Get property alias
        property_alias = input_return["property_alias"]
        logger.info(f"Extracting information for property {property_alias}")
        try:
            property_data = resolve_property_data(orgs_data, organization, property_alias)
            property = property_data["property"]["name"]
            property_short_code = property_data["property"]["short_code"]
            property_id = property_data["property"]["id"]
            organization_id = property_data["organization"]["id"]
        except Exception as e:
            error_count += 1
            logger.error(f"Error resolving property information: {e}")
            continue

        # Step 3: Generate output CS
        logger.info(f"Generating output for property {property}")
        params = {
            "Property" : property_short_code,
            "DueFor": timeframe
        }
        with open(DEFAULT_OUTPUT_SCHEMA, "r") as f:
            output_schema_data = json.load(f)

        try:
            output_file_name = f"{organization_id} {property_id} {property_short_code} {timeframe} SCHEDULE.csv"
            logger.info(f"Generating output file {output_file_name}")
            df_output = generate_output_df(df_input, output_schema_data, "rd_project_worksheet", "subsidy_base", params)
            df_output.to_csv(os.path.join(OUTPUT_DIR, output_file_name), index=False)
        except Exception as e:
            error_count += 1
            logger.error(f"Error generating output for file {pdf_file}: {e}")
            continue
        ok_count += 1

        # Step 4: Rename and move processed file
        logger.info(f"Moving processed file to processed folder")
        processed_dir = Path(pdf_file).parent.parent / f"processed/{timeframe}"
        processed_dir.mkdir(parents=True, exist_ok=True)
        processed_file_path = processed_dir / f"processed_{property_short_code}_{timeframe}.pdf"
        os.rename(pdf_file, processed_file_path)
    logger.info(f"*** File processing summary ***")
    logger.info(f"Total: {file_count:03d}; OK: {ok_count:03d}; Errors: {error_count:03d}")
    logger.info("********PDF processing completed********")

if __name__ == "__main__":
    main()


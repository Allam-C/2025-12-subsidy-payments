import re
from datetime import datetime
from utils import dates_match

def find_table_header_index(lines, header_keywords):
    """
    Finds the index of the header line in a list of text lines.
    Assumes the header contains specific keywords.
    """
    for i, line in enumerate(lines):
        matches = sum(1 for w in header_keywords if w in line)
        if matches >= 2:
            return i
    return None

def find_table_end_index(lines, start_index):
    """
    Finds the index where the table ends, starting from the header index.
    """
    for i, line in enumerate(lines[start_index+1:], start=start_index+1):
        cleaned = line.strip()

        # End conditions
        if cleaned.startswith("Sensitive but"):
            return i
        if cleaned.startswith("TOTALS:"):
            return i
        if cleaned.startswith("===="):
            return i
        if cleaned.startswith("PAYMENT"):
            return i
    return len(lines)

def extract_table_lines(lines, start_index, end_index=None):
    """
    Extracts table lines starting from the header index.
    """
    rows = []
    for line in lines[start_index+1:end_index]:
        if line.strip() == "":
            break
        if set(line.strip()) in [{"-"}, {"_"}]:  
            continue
        rows.append(line)
    return rows

def validate_file(lines, validation_rules):
    """
    Confirms the presence of a keyword in a specific row to validate the file.
    """
    keyword = validation_rules.get("keyword")
    row_index = validation_rules.get("keyword_row")
    if row_index < 0 or row_index >= len(lines):
        raise IndexError(f"Keyword row index {row_index} is out of bounds.")
    line = lines[row_index-1]
    return keyword in line

def validate_date(lines, validation_rules, date_param):
    date_rule = validation_rules.get("date")
    if not date_rule:
        return False  # No date rule provided
    row_index = date_rule.get("row")
    if row_index < 0 or row_index >= len(lines):
        raise IndexError(f"Date row index {row_index} is out of bounds.")
    line = lines[row_index-1]
    date_str = line.split(":",1)[1].strip()
    return dates_match(date_param, date_str)

def parse_line(line, schema):
    raw_cells = re.split(r"\s+", line.strip())
    expected_cols = schema["columns"]
    parsed = []
    raw_index = 0
    for i, col in enumerate(expected_cols):
        col_type = col.get("type","str")
        dynamic = col.get("dynamic_length_string", False)
        optional = col.get("optional", False)
        if dynamic:
            name_parts = []
            while raw_index < len(raw_cells):
                token = raw_cells[raw_index]
                if re.match(r"^-?\d+(\.\d+)?$", token):  # numeric token
                    break
                name_parts.append(token)
                raw_index += 1
            parsed.append(" ".join(name_parts) if name_parts else None)
        elif col_type == 'str':
            if raw_index < len(raw_cells):
                parsed.append(raw_cells[raw_index] or None)
                raw_index += 1
            else:
                parsed.append(None)
        elif col_type == "int":
            if raw_index < len(raw_cells):
                try:
                    parsed.append(int(raw_cells[raw_index]))
                    raw_index += 1
                except (ValueError, IndexError):
                    parsed.append(None)
            else:
                parsed.append(None)
        elif col_type == "date":
            if raw_index < len(raw_cells):
                try:
                    val = datetime.strptime(raw_cells[raw_index], "%m/%d/%Y")
                    parsed.append(raw_cells[raw_index])
                    raw_index += 1
                except (ValueError, IndexError):
                    parsed.append(None)
            else:
                parsed.append(None)
        elif col_type == "float":
            if raw_index < len(raw_cells):
                try:
                    parsed.append(float(raw_cells[raw_index]))
                    raw_index += 1
                except ValueError:
                    parsed.append(None)                
            else:
                parsed.append(None)
    return parsed

import json
import pytest
from schema_utils import (
    get_file_validation,
    get_table_schema,
    get_column_names
)

# Load schema once for all tests
@pytest.fixture
def schema():
    with open("schemas/input.json", "r") as f:
        return json.load(f)

def test_get_file_validation_returns_date_block(schema):
    file_id = schema["files"][0]["id"]

    validation = get_file_validation(schema, file_id)

    # Ensure validation block exists
    assert isinstance(validation, dict)
    assert "keyword" in validation
    assert "keyword_row" in validation
    assert "date" in validation

    date_block = validation["date"]

    # Validate required fields
    assert "row" in date_block
    assert isinstance(date_block["row"], int)

    assert "format" in date_block
    assert isinstance(date_block["format"], str)


def test_get_table_schema_valid(schema):
    file_id = schema["files"][0]["id"]
    table_id = schema["files"][0]["tables"][0]["id"]

    table_schema = get_table_schema(schema, file_id, table_id)

    assert isinstance(table_schema, dict)
    assert "columns" in table_schema
    assert isinstance(table_schema["columns"], list)


def test_get_table_schema_invalid_file(schema):
    with pytest.raises(ValueError):
        get_table_schema(schema, "nonexistent_file", "some_table")


def test_get_table_schema_invalid_table(schema):
    file_id = schema["files"][0]["id"]
    with pytest.raises(ValueError):
        get_table_schema(schema, file_id, "nonexistent_table")


def test_get_column_names_input(schema):
    file_id = schema["files"][0]["id"]
    table_id = schema["files"][0]["tables"][0]["id"]

    cols = get_column_names(schema, file_id, table_id, direction="input")

    assert isinstance(cols, list)
    assert all(isinstance(c, str) for c in cols)


# def test_get_column_names_output(schema):
#     file_id = schema["files"][0]["id"]
#     table_id = schema["files"][0]["tables"][0]["id"]

#     # Only run this test if output_name exists in schema
#     table_schema = get_table_schema(schema, file_id, table_id)
#     if "output_name" in table_schema["columns"][0]:
#         cols = get_column_names(schema, file_id, table_id, direction="output")
#         assert isinstance(cols, list)
#         assert all(isinstance(c, str) for c in cols)
#     else:
#         pytest.skip("Schema does not define output_name fields")
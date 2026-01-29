
def get_column_names(schema,file_id,table_id,direction="input"):
    """
    Retrieves the column names for a specific table from the schema data.
    """
    table_schema = get_table_schema(schema, file_id, table_id)
    if direction == "output":
        return [col["output_name"] for col in table_schema["columns"]]
    return [col["name"] for col in table_schema["columns"]]

def get_table_schema(schema_data, file_id, table_id):
    """
    Retrieves the schema for a specific table from the schema data.
    """
    for file in schema_data.get("files", []):
        if file["id"] == file_id:
            for table in file.get("tables", []):
                if table["id"] == table_id:
                    return table
            raise ValueError(f"Table with id {table_id} not found in schema.")
    raise ValueError(f"File with id {file_id} not found in schema.")

def get_file_schema(schema_data, file_id):
    """
    Retrieves the schema for a specific file from the schema data.
    """
    for file in schema_data.get("files", []):
        if file["id"] == file_id:
            return file
    raise ValueError(f"File with id {file_id} not found in schema.")

def get_file_validation(schema_data, file_id):
    """
    Retrieves the validation rules for a specific file from the schema data.
    """
    for file in schema_data.get("files", []):
        if file["id"] == file_id:
            return file.get("validation", {})
    raise ValueError(f"File with id {file_id} not found in schema.")

def get_property_name_configuration(schema_data, file_id):
    """
    Retrieves the property name configuration from the schema data.
    """
    for file in schema_data.get("files", []):
        if file["id"] == file_id:
            if "property" not in file:
                raise ValueError(f"Property configuration not found for file id {file_id}.")
            if not file.get("property", {}):
                raise ValueError(f"Property configuration is empty for file id {file_id}.")
            return file.get("property", {})
    raise ValueError(f"File with id {file_id} not found in schema.")
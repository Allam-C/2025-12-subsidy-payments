def get_org_by_short_code(orgs_data, short_code):
    sc = short_code.strip().lower()
    for org in orgs_data.get("organizations", []):
        if org.get("short_name", "").lower() == sc:
            return org
    raise ValueError(f"Organization with short_code '{short_code}' not found.")

def get_property_by_alias(org_data, property_alias):
    alias = property_alias.strip().lower()
    for prop in org_data.get("properties", []):
        if prop.get("alias", "").strip().lower() == alias:
            return prop
    raise ValueError(f"Property with alias '{property_alias}' not found in organization '{org_data.get('name', '')}'.")
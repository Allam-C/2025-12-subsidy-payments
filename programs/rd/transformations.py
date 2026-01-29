def identity(df):
    return df

def apply_surcharge_logic(df):
    df = df[df["surcharge"] > 0].copy()
    df.loc[:,"surcharge"] = -df["surcharge"].abs()
    return df

TRANSFORMATIONS_MAP = {
    "identity": identity,
    "apply_surcharge_logic": apply_surcharge_logic
}
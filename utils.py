from datetime import datetime

def dates_match(date_param, date_file):
    try:
        dt_param = datetime.strptime(date_param, "%Y%m")
        dt_file = datetime.strptime(date_file, "%m/%d/%Y")
        return dt_param.year == dt_file.year and dt_param.month == dt_file.month
    except ValueError as e:
        return False

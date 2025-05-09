from datetime import datetime, timedelta

def format_date_time(date):
    if isinstance(date, str):
        dt = datetime.fromisoformat(date)
    else:
        dt = date
    return dt.replace(microsecond=0).isoformat(" ", timespec="seconds")
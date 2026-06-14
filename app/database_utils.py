import datetime

def format_medical_date(dt: datetime.datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")
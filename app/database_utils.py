import datetime

def format_medical_date(dt: datetime.datetime) -> str:
    """Гарно форматує дату для виведення в електронному рецепті"""
    return dt.strftime("%d.%m.%Y %H:%M")
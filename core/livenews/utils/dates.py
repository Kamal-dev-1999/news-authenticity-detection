from django.utils.dateparse import parse_datetime
from django.utils import timezone

def safe_parse_date(date_input):
    """Safely parse dates from API responses"""
    if isinstance(date_input, str):
        try:
            return parse_datetime(date_input)
        except (ValueError, TypeError):
            pass
    elif isinstance(date_input, (int, float)):
        try:
            return timezone.datetime.fromtimestamp(date_input)
        except (ValueError, TypeError):
            pass
    return timezone.now()
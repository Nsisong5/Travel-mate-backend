from datetime import datetime,date


def get_duration(start_date: str, end_date: str, date_format: str = "%Y-%m-%d") -> int:
    """
    Calculate the duration of a trip in days given start and end dates.

    Args:
        start_date (str): Trip start date as a string (default format: YYYY-MM-DD).
        end_date (str): Trip end date as a string (default format: YYYY-MM-DD).
        date_format (str): Format of the provided date strings. Defaults to "%Y-%m-%d".

    Returns:
        int: Duration in days (inclusive of both start and end date).
    """
    start = datetime.strptime(start_date, date_format)
    end = datetime.strptime(end_date, date_format)

    duration = (end - start).days + 1  # +1 if you want to count both start & end days
    return duration
    
def calculate_duration(start_date: date, end_date: date) -> str:
    """Calculate trip duration in days"""
    delta = end_date - start_date
    days = delta.days
    if days == 1:
        return "1 day"
    return f"{days} days"    
    
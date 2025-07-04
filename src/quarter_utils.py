from datetime import datetime
from typing import Tuple


def get_current_quarter_and_year() -> Tuple[str, str]:
    """
    Determine the current Drexel quarter and year based on the current date.
    
    Drexel quarters:
    - Fall (15): Late September - Mid December
    - Winter (25): Early January - Late March
    - Spring (35): Late March/Early April - Mid June
    - Summer (45): Late June - Early September
    
    Returns:
        Tuple of (year, quarter_code) as strings
    """
    now = datetime.now()
    month = now.month
    day = now.day
    year = now.year
    
    # Determine quarter based on month and day
    if month == 1 or month == 2 or (month == 3 and day <= 22):
        # Winter quarter
        quarter = "25"
    elif (month == 3 and day > 22) or month == 4 or month == 5 or (month == 6 and day <= 14):
        # Spring quarter
        quarter = "35"
    elif (month == 6 and day > 14) or month == 7 or month == 8 or (month == 9 and day <= 22):
        # Summer quarter
        quarter = "45"
    else:
        # Fall quarter (Sept 23 - Dec 31)
        quarter = "15"
    
    # For Fall quarter, if we're in September-December, it's the current year
    # For other quarters in January-August, they belong to the current year
    return str(year), quarter


def get_quarter_name(quarter_code: str) -> str:
    """Get the human-readable name for a quarter code."""
    quarter_names = {
        "15": "Fall",
        "25": "Winter",
        "35": "Spring",
        "45": "Summer"
    }
    return quarter_names.get(quarter_code, "Unknown")


if __name__ == "__main__":
    # Test the function
    year, quarter = get_current_quarter_and_year()
    quarter_name = get_quarter_name(quarter)
    print(f"Current quarter: {quarter_name} {year} (code: {quarter})")
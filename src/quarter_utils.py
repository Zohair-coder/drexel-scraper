"""Utilities for determining the current Drexel quarter based on date."""

from datetime import datetime


def get_current_quarter_and_year() -> tuple[str, str]:
    """
    Determine the current Drexel quarter and year based on the current date.

    Drexel quarters:
    - Fall (15): July 1 - September 27
    - Winter (25): September 28 - January 15
    - Spring (35): January 16 - April 14
    - Summer (45): April 15 - June 30

    Returns:
        Tuple of (year, quarter_code) as strings
    """
    now = datetime.now()
    month = now.month
    day = now.day
    year = now.year

    # Determine quarter based on month and day
    if month == 7 or month == 8 or (month == 9 and day <= 27):
        # Fall quarter
        quarter = "15"
    elif (
        (month == 9 and day >= 28)
        or month == 10
        or month == 11
        or month == 12
        or (month == 1 and day <= 15)
    ):
        # Winter quarter
        quarter = "25"
    elif (
        (month == 1 and day >= 16)
        or month == 2
        or month == 3
        or (month == 4 and day <= 14)
    ):
        # Spring quarter
        quarter = "35"
    else:
        # Summer quarter (April 15 - June 30)
        quarter = "45"

    # For Winter quarter spanning two calendar years (Sept 28 - Jan 15),
    # if we're in January, it belongs to the previous year's academic year
    if quarter == "25" and month == 1:
        year = year - 1

    # For Spring quarter (Jan 16 - Apr 14), the academic year started the 
    # previous Fall, so use previous calendar year for the code
    # e.g., Jan 2026 → Spring of academic year 2025-2026 → code 202535
    if quarter == "35":
        year = year - 1

    return str(year), quarter


def get_previous_quarter(year: str, quarter: str) -> tuple[str, str]:
    """Get the previous quarter given a year and quarter code."""
    quarter_order = ["15", "25", "35", "45"]  # Fall, Winter, Spring, Summer
    current_idx = quarter_order.index(quarter)
    
    if current_idx == 0:
        # Fall -> previous Summer (same year)
        return year, "45"
    elif quarter == "25":
        # Winter -> previous Fall (same academic year)
        return year, "15"
    else:
        # Spring -> Winter, Summer -> Spring (may need year adjustment)
        prev_quarter = quarter_order[current_idx - 1]
        if prev_quarter == "25":
            # Winter is in previous calendar year for Jan dates
            return str(int(year) - 1), prev_quarter
        return year, prev_quarter


def get_quarter_name(quarter_code: str) -> str:
    """Get the human-readable name for a quarter code."""
    quarter_names = {
        "15": "Fall",
        "25": "Winter",
        "35": "Spring",
        "45": "Summer",
    }
    return quarter_names.get(quarter_code, "Unknown")


if __name__ == "__main__":
    # Test the function
    year, quarter = get_current_quarter_and_year()
    quarter_name = get_quarter_name(quarter)
    print(f"Current quarter: {quarter_name} {year} (code: {quarter})")

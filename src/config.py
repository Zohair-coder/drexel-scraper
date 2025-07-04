import os
import sys
from datetime import datetime
import pytz

def get_quarter_and_year_for_date(date_obj):
    """
    Determine the Drexel quarter and year for a given date.
    
    Drexel quarter system:
    - Fall (15): September - December
    - Winter (25): January - March
    - Spring (35): March - June
    - Summer (45): June - September
    
    Args:
        date_obj: datetime object
        
    Returns:
        tuple: (year, quarter) where year is string and quarter is string
    """
    month = date_obj.month
    year = date_obj.year
    
    # Determine quarter based on month
    if month >= 9:  # September - December (Fall)
        quarter = "15"
        return str(year), quarter
    elif month >= 6:  # June - August (Summer)
        quarter = "45"
        return str(year), quarter
    elif month >= 3:  # March - May (Spring)
        quarter = "35"
        return str(year), quarter
    else:  # January - February (Winter)
        quarter = "25"
        return str(year), quarter

def get_current_quarter_and_year():
    """
    Automatically determine the current Drexel quarter and year based on the current date.
    
    Returns:
        tuple: (year, quarter) where year is string and quarter is string
    """
    # Use Eastern Time Zone since Drexel is in Philadelphia
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    return get_quarter_and_year_for_date(now)

# Automatically determine current quarter and year
year, quarter = get_current_quarter_and_year()

# in format YYYY (e.g. 2022)
# example value: 2022
# year = "2024"  # Now automatically determined
# 15 for Fall, 25 for Winter, 35 for Spring, 45 for Summer
# example value: 45
# quarter = "45"  # Now automatically determined

print(f"Auto-detected current quarter: {quarter} for year: {year}")

# check college code by going to the tms website and selecting your college from the left sidebar
# the URL bar should update and it should end with something like collCode=CI
# the characters after the = sign is your college code
# e.g. in this URL the college code is CI
# https://termmasterschedule.drexel.edu/webtms_du/collegesSubjects/202245?collCode=CI
# NOTE: This configuration will be ignored if the --all-colleges flag is used
# example values = CI, A, AS
college_code = "CI"

# Warn users if they have missing required environment variables
environ_help_url = (
    "https://github.com/Zohair-coder/drexel-scraper?tab=readme-ov-file#authentication"
)


def get_environ(key: str, required: bool = True) -> str:
    if key in os.environ:
        return os.environ[key]
    elif required:
        print(
            f"{key} is missing from your environment variables and is required to run this script. See {environ_help_url} for more information and help."
        )
        sys.exit(1)
    else:
        return ""


# Drexel Connect Credentials
drexel_email = get_environ("DREXEL_EMAIL")
drexel_password = get_environ("DREXEL_PASSWORD")
# This is not required if the user is using a separate authenticator app and will manually approve the login attempt
drexel_mfa_secret_key = get_environ("DREXEL_MFA_SECRET_KEY", False) or None

# URL's
tms_base_url = "https://termmasterschedule.drexel.edu"
tms_home_url = tms_base_url + "/webtms_du"
tms_quarter_url = tms_home_url + "/collegesSubjects/" + year + quarter

drexel_connect_base_url = "https://connect.drexel.edu"

# Email AWS Configuration
topic_arn = os.getenv("DREXEL_SCHEDULER_TOPIC_ARN")
sns_endpoint = os.getenv("SNS_ENDPOINT_URL", None)


# element attribute dictionaries the soup will look for
class attributes:
    rows = {"role": "row"}


def get_college_page_url(college_name: str) -> str:
    return tms_quarter_url + "?collCode=" + college_name

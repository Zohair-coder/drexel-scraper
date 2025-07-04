import os
import sys

from quarter_utils import get_current_quarter_and_year, get_quarter_name

# Automatically determine the current quarter and year
# Can be overridden with DREXEL_YEAR and DREXEL_QUARTER environment variables
if "DREXEL_YEAR" in os.environ and "DREXEL_QUARTER" in os.environ:
    year = os.environ["DREXEL_YEAR"]
    quarter = os.environ["DREXEL_QUARTER"]
    print(
        f"Using manually configured {get_quarter_name(quarter)} {year} "
        f"quarter (code: {quarter})"
    )
else:
    year, quarter = get_current_quarter_and_year()
    print(
        f"Using auto-detected {get_quarter_name(quarter)} {year} "
        f"quarter (code: {quarter})"
    )

# Note: These values are now automatically determined based on the current date
# Fall (15): July 1 - September 27
# Winter (25): September 28 - January 15
# Spring (35): January 16 - April 14
# Summer (45): April 15 - June 30
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

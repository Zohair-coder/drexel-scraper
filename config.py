# in format YYYY (e.g. 2022)
# example value: 2022
year = "2023"
# 15 for Fall, 25 for Winter, 35 for Spring, 45 for Summer
# example value: 45
quarter = "25"
# check college code by going to the tms website and selecting your college from the left sidebar
# the URL bar should update and it should end with something like collCode=CI
# the characters after the = sign is your college code
# e.g. in this URL the college code is CI
# https://termmasterschedule.drexel.edu/webtms_du/collegesSubjects/202245?collCode=CI
# NOTE: This configuration will be ignored if the --all-colleges flag is used
# example values = CI, A, AS
college_code = "CI"

# URL's
tms_base_url = "https://termmasterschedule.drexel.edu"
tms_home_url = tms_base_url + "/webtms_du"
tms_quarter_url = tms_home_url + "/collegesSubjects/" + year + quarter


# element attribute dictionaries the soup will look for
class attributes:
    rows = {
        "role": "row"
    }


def get_college_page_url(college_name):
    return tms_quarter_url + "?collCode=" + college_name

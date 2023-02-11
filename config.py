year = "2022"
quarter = "45"
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

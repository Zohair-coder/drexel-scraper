from bs4 import BeautifulSoup
from config import attributes
from ratings import rating
from datetime import datetime


def parse(html, data: dict, include_ratings: bool = False):

    soup = BeautifulSoup(html, "html.parser")
    table_rows = soup.find_all("tr", class_=["odd", "even"])

    ratings_cache = {}

    for table_row in table_rows:
        row_data = table_row.find_all("td")

        row_data_strs = [fix_encoding_issue(
            data.text).strip() for data in row_data]

        crn = row_data_strs[5]

        start_time, end_time = parse_time(row_data_strs[9])

        data[crn] = {
            "subject_code": row_data_strs[0],
            "course_number": row_data_strs[1],
            "instruction_type": row_data_strs[2],
            "instruction_method": row_data_strs[3],
            "section": row_data_strs[4],
            "crn": row_data_strs[5],
            "enroll": get_enroll(row_data[5]),
            "max_enroll": get_max_enroll(row_data[5]),
            "course_title": row_data_strs[6],
            "days": row_data_strs[8],
            "start_time": start_time,
            "end_time": end_time,
            "instructors": get_instructors(row_data_strs[-1]),
        }

        print("Parsed CRN: " + crn)

        if include_ratings:
            for index, instructor in enumerate(data[crn]["instructors"]):

                print("Getting rating for " + instructor["name"])

                name_tokens = instructor["name"].split(" ")
                name = name_tokens[0] + " " + name_tokens[-1]

                if name not in ratings_cache:
                    ratings_cache[name] = rating(name)

                rating_obj = ratings_cache[name]

                data[crn]["instructors"][index]["rating"] = rating_obj
                print("Done")

        print()

    return data


def get_instructors(instructors_str: str) -> list:
    instructors = []
    for instructor in instructors_str.split(","):
        instructors.append({
            "name": instructor.strip(),
        })
    return instructors


def get_enroll(td):
    span = td.contents[0]
    title_attr = span.attrs["title"]

    if "FULL" in title_attr:
        return "FULL"

    enroll = title_attr.split(";")[1]
    return enroll.split("=")[1]


def get_max_enroll(td):
    span = td.contents[0]
    title_attr = span.attrs["title"]

    if "FULL" in title_attr:
        return "FULL"

    enroll = title_attr.split(";")[0]
    return enroll.split("=")[1]


def fix_encoding_issue(text: str) -> str:
    return text.replace("\xa0", " ")


def parse_time(t: str):
    if t == "TBD":
        return (None, None)
    start_str, end_str = t.split(" - ")
    start_time = time_str_to_object(start_str)
    end_time = time_str_to_object(end_str)
    return (start_time.isoformat(), end_time.isoformat())


def time_str_to_object(t: str):
    return datetime.strptime(t, "%I:%M %p")

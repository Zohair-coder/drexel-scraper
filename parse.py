from bs4 import BeautifulSoup
from config import attributes
from ratings import rating
from datetime import datetime
import json
import os

def parse(html, data: dict, include_ratings: bool = False):

    soup = BeautifulSoup(html, "html.parser")
    table_rows = soup.find_all("tr", class_=["odd", "even"])

    try:
        with open("cache/ratings_cache.json", "r") as f:
            print("Found cached ratings...")
            ratings_cache = json.load(f)
    except FileNotFoundError:
        print("No cached ratings found...")
        ratings_cache = {}

    for table_row in table_rows:
        row_data = table_row.find_all("td")

        row_data_strs = [fix_encoding_issue(
            data.text).strip() for data in row_data]

        crn = row_data_strs[5]

        print("Parsing CRN: " + crn + " (" + row_data_strs[6] + ")...")

        start_time, end_time = parse_time(row_data_strs[9])
        days = parse_days(row_data_strs[8])

        data[crn] = {
            "subject_code": row_data_strs[0],
            "course_number": row_data_strs[1],
            "instruction_type": row_data_strs[2],
            "instruction_method": row_data_strs[3],
            "section": row_data_strs[4],
            "crn": int(row_data_strs[5]),
            "enroll": get_enroll(row_data[5]),
            "max_enroll": get_max_enroll(row_data[5]),
            "course_title": row_data_strs[6],
            "days": days,
            "start_time": start_time,
            "end_time": end_time,
            "instructors": get_instructors(row_data_strs[-1], include_ratings, ratings_cache),
        }

        print("Parsed CRN: " + crn + " (" + row_data_strs[6] + ")")
        print()

    if not os.path.exists("cache"):
        os.makedirs("cache")

    with open("cache/ratings_cache.json", "w") as f:
        json.dump(ratings_cache, f, indent=4)

    return data


def get_instructors(instructors_str: str, include_ratings: bool, ratings_cache: dict) -> list or None:
    if instructors_str == "STAFF":
        return None

    instructors = []
    for instructor in instructors_str.split(","):
        name = instructor.strip()

        if include_ratings:
            name_tokens = name.split(" ")
            rmp_name = name_tokens[0] + " " + name_tokens[-1]

            if rmp_name not in ratings_cache:
                print("Rating not found in cache for " + rmp_name + ". Fetching...")
                ratings_cache[rmp_name] = rating(rmp_name)
                if ratings_cache[rmp_name] is None and len(name_tokens) > 2:
                    rmp_name = name_tokens[0] + " " + name_tokens[1]
                    ratings_cache[rmp_name] = rating(rmp_name)
            else:
                print("Found cached rating for " + rmp_name + "...")

            rating_obj = ratings_cache[rmp_name]

            instructors.append({
                "name": name,
                "rating": rating_obj,
            })

        else:
            instructors.append({
                "name": name,
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


def parse_days(d: str):

    if d == "TBD":
        return None

    days = []
    mapping = {
        "M": "Monday",
        "T": "Tuesday",
        "W": "Wednesday",
        "R": "Thursday",
        "F": "Friday",
        "S": "Saturday",
        "U": "Sunday",
    }

    for day in d:
        days.append(mapping[day])

    return days


def parse_time(t: str):
    if t == "TBD":
        return (None, None)
    start_str, end_str = t.split(" - ")
    start_time = time_str_to_object(start_str)
    end_time = time_str_to_object(end_str)
    return (time_obj_to_str(start_time), time_obj_to_str(end_time))


def time_str_to_object(t: str):
    return datetime.strptime(t, "%I:%M %p")


def time_obj_to_str(t: datetime):
    return t.strftime("%H:%M")

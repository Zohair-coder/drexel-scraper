from bs4 import BeautifulSoup
from bs4.element import Tag
from drexel_scraper.ratings import rating
from datetime import datetime
import re
from typing import Any


def parse_subject_page(
    html: str,
    data: dict[str, dict[str, Any]],
    include_ratings: bool = False,
    ratings_cache: dict[str, dict[str, int] | None] = {},
) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    table_rows = soup.find_all("tr", class_=["odd", "even"])

    parsed_crns = {}
    for table_row in table_rows:
        row_data = table_row.find_all("td")

        row_data_strs = [fix_encoding_issue(data.text).strip() for data in row_data]

        crn = row_data_strs[5]

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
            "instructors": get_instructors(
                row_data_strs[-1], include_ratings, ratings_cache
            ),
        }

        parsed_crns[crn] = row_data[5].find("a")["href"]

    return parsed_crns


def parse_crn_page(html: str, data: dict[str, dict[str, Any]]) -> None:
    soup = BeautifulSoup(html, "html.parser")

    # Extract credits
    table_datas = soup.find_all("td", class_=["odd", "even"])

    credits = table_datas[4].text.strip()
    crn = table_datas[0].text.strip()

    # Extract prereqs
    prereqs_heading_element = soup.find(
        "b", string=re.compile("pre-requisites:", re.IGNORECASE)
    )

    sibling_texts = []
    if prereqs_heading_element is not None:
        for sibling in prereqs_heading_element.next_siblings:
            if isinstance(sibling, Tag) and sibling.name == "span":
                sibling_texts.append(sibling.text.strip())

    prereqs = " ".join(sibling_texts)

    data[crn]["prereqs"] = prereqs
    data[crn]["credits"] = credits


def get_instructors(
    instructors_str: str,
    include_ratings: bool,
    ratings_cache: dict[str, dict[str, int] | None],
) -> list[dict[str, Any]] | None:
    if instructors_str == "STAFF":
        return None

    instructors = []
    for instructor in instructors_str.split(","):
        name = instructor.strip()

        if include_ratings:
            # Search for first word and last word in name first
            # If that doesn't work, try first two words
            # If that still doesn't work, don't include rating

            name_tokens = name.split(" ")
            rmp_name = name_tokens[0] + " " + name_tokens[-1]

            if name not in ratings_cache:
                ratings_cache[name] = rating(rmp_name)
                if ratings_cache[name] is None and len(name_tokens) > 2:
                    rmp_name = name_tokens[0] + " " + name_tokens[1]
                    ratings_cache[name] = rating(rmp_name)

            rating_obj = ratings_cache[name]

            instructors.append(
                {
                    "name": name,
                    "rating": rating_obj,
                }
            )

        else:
            instructors.append(
                {
                    "name": name,
                }
            )

    return instructors


def get_enroll(td: Tag) -> str:
    span = td.contents[0]

    if not isinstance(span, Tag):
        raise Exception("Enrollment HTML span tag inside td not structured as expected")

    title_attr = span.attrs["title"]

    if "FULL" in title_attr:
        return "FULL"

    enroll = title_attr.split(";")[1]
    return enroll.split("=")[1]


def get_max_enroll(td: Tag) -> str:
    span = td.contents[0]

    if not isinstance(span, Tag):
        raise Exception(
            "Max enrollment HTML span tag inside td not structured as expected"
        )

    title_attr = span.attrs["title"]

    if "FULL" in title_attr:
        return "FULL"

    enroll = title_attr.split(";")[0]
    return enroll.split("=")[1]


def fix_encoding_issue(text: str) -> str:
    return text.replace("\xa0", " ")


def parse_days(d: str) -> list[str] | None:
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


def parse_time(t: str) -> tuple[str | None, str | None]:
    if t == "TBD":
        return (None, None)
    start_str, end_str = t.split(" - ")
    start_time = time_str_to_object(start_str)
    end_time = time_str_to_object(end_str)
    return (time_obj_to_str(start_time), time_obj_to_str(end_time))


def time_str_to_object(t: str) -> datetime:
    return datetime.strptime(t, "%I:%M %p")


def time_obj_to_str(t: datetime) -> str:
    return t.strftime("%H:%M")

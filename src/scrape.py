from requests import Session, Response
from bs4 import BeautifulSoup
import json
import os
from typing import Any
import time

from helpers import send_request
from parse import parse_subject_page, parse_crn_page
import config
import login
from quarter_utils import get_previous_quarter, get_quarter_name


def check_quarter_available(session: Session, year: str, quarter: str) -> bool:
    """Check if a quarter's schedule is available on TMS."""
    url = config.tms_home_url + f"/collegesSubjects/{year}{quarter}"
    try:
        response = send_request(session, url)
        if "not available online" in response.text.lower():
            return False
        # Check for actual content (college links)
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=lambda h: h and "collCode" in h)
        return len(links) > 0
    except Exception:
        return False


def find_available_quarter(session: Session, start_year: str, start_quarter: str) -> tuple[str, str]:
    """Find the most recent available quarter, starting from the given one."""
    year, quarter = start_year, start_quarter
    attempts = 0
    max_attempts = 8  # Don't go back more than 2 years
    
    while attempts < max_attempts:
        print(f"Checking if {get_quarter_name(quarter)} {year} ({year}{quarter}) is available...")
        if check_quarter_available(session, year, quarter):
            return year, quarter
        print("  → Not available, trying previous quarter...")
        year, quarter = get_previous_quarter(year, quarter)
        attempts += 1
    
    raise Exception(f"Could not find an available quarter after {max_attempts} attempts")


def scrape(
    include_ratings: bool = False, all_colleges: bool = False
) -> dict[str, dict[str, Any]]:
    session = Session()

    print("Signing in...")
    is_logged_into_drexel_connect = False
    failiure_count = 0
    reset_period = 1  # seconds
    while not is_logged_into_drexel_connect:
        reset_period *= 2
        try:
            session = login.login_with_drexel_connect(session)
            is_logged_into_drexel_connect = True
        except Exception:
            print("Error logging in to Drexel Connect: ")
            # not printing stack trace in case password gets accidentally logged
            print(f"Trying again in {reset_period} seconds...")

            failiure_count += 1
            if failiure_count > 8:
                raise Exception(
                    "Failed to log in to Drexel Connect after {} attempts".format(
                        failiure_count
                    )
                )

            time.sleep(reset_period)

    # Check if the configured quarter is available, fall back if not
    print("\nValidating quarter availability...")
    available_year, available_quarter = find_available_quarter(
        session, config.year, config.quarter
    )
    
    if available_year != config.year or available_quarter != config.quarter:
        print(f"\n⚠️  Configured quarter {get_quarter_name(config.quarter)} {config.year} is not available!")
        print(f"    Falling back to {get_quarter_name(available_quarter)} {available_year}")
        # Update the config module's values for this run
        config.year = available_year
        config.quarter = available_quarter
        config.tms_quarter_url = config.tms_home_url + "/collegesSubjects/" + available_year + available_quarter
    else:
        print(f"✓ Quarter {get_quarter_name(config.quarter)} {config.year} is available!\n")

    data: dict[str, dict[str, Any]] = {}

    if not all_colleges:
        college_codes = [config.college_code]
    else:
        college_codes = get_all_college_codes(session)

    for college_code in college_codes:
        response = go_to_college_page(session, college_code)
        scrape_all_subjects(session, data, response.text, include_ratings)

    return data


def get_all_college_codes(session: Session) -> list[str]:
    response = send_request(session, config.get_college_page_url(""))
    soup = get_soup(response.text)
    college_codes = []

    for link in soup.find_all(
        "a", href=lambda href: href and href.startswith("/webtms_du/collegesSubjects")
    ):
        college_codes.append(link["href"].split("=")[-1])

    return college_codes


def get_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def go_to_college_page(session: Session, college_code: str) -> Response:
    return send_request(session, config.get_college_page_url(college_code))


def scrape_all_subjects(
    session: Session, data: dict[str, dict[str, Any]], html: str, include_ratings: bool
) -> dict[str, dict[str, Any]]:
    try:
        with open("cache/extra_course_data_cache.json", "r") as f:
            extra_course_data_cache = json.load(f)
    except FileNotFoundError:
        extra_course_data_cache = {}

    try:
        with open("cache/ratings_cache.json", "r") as f:
            ratings_cache = json.load(f)
    except FileNotFoundError:
        ratings_cache = {}

    college_page_soup = get_soup(html)
    for subject_page_link in college_page_soup.find_all(
        "a", href=lambda href: href and href.startswith("/webtms_du/courseList")
    ):
        try:
            response = send_request(
                session, config.tms_base_url + subject_page_link["href"]
            )
            parsed_crns = parse_subject_page(
                response.text, data, include_ratings, ratings_cache
            )
        except Exception as e:
            raise Exception(
                "Error scraping/parsing subject page: {}".format(
                    subject_page_link["href"]
                )
            ) from e

        for crn, crn_page_link in parsed_crns.items():
            if crn in extra_course_data_cache:
                data[crn]["credits"] = extra_course_data_cache[crn]["credits"]
                data[crn]["prereqs"] = extra_course_data_cache[crn]["prereqs"]
            else:
                try:
                    response = send_request(
                        session, config.tms_base_url + crn_page_link
                    )
                    parse_crn_page(response.text, data)
                except Exception as e:
                    raise Exception(
                        "Error scraping/parsing CRN {}: {}".format(crn, crn_page_link)
                    ) from e

                extra_course_data_cache[crn] = {
                    "credits": data[crn]["credits"],
                    "prereqs": data[crn]["prereqs"],
                }

            print("Parsed CRN: " + crn + " (" + data[crn]["course_title"] + ")")
            print()

    if not os.path.exists("cache"):
        os.makedirs("cache")

    with open("cache/ratings_cache.json", "w") as f:
        json.dump(ratings_cache, f, indent=4)

    with open("cache/extra_course_data_cache.json", "w") as f:
        json.dump(extra_course_data_cache, f, indent=4)

    return data

from requests import Session
from bs4 import BeautifulSoup
import json
import os

from parse import parse_subject_page, parse_crn_page
import config


def scrape(include_ratings: bool = False, all_colleges: bool = False):
    session = Session()
    data = {}

    if not all_colleges:
        college_codes = [config.college_code]
    else:
        college_codes = get_all_college_codes(session)

    for college_code in college_codes:
        response = go_to_college_page(session, college_code)
        scrape_all_subjects(session, data, response.text, include_ratings)

    return data


def get_all_college_codes(session: Session):
    response = session.get(config.get_college_page_url(""))
    soup = get_soup(response.text)
    college_codes = []

    for link in soup.find_all("a", href=lambda href: href and href.startswith("/webtms_du/collegesSubjects")):
        college_codes.append(link["href"].split("=")[-1])

    return college_codes


def get_soup(html):
    return BeautifulSoup(html, "html.parser")


def go_to_college_page(session: Session, college_code: str):
    resp = session.get(config.get_college_page_url(college_code))
    resp.raise_for_status()
    return resp


def scrape_all_subjects(session: Session, data: dict, html: str, include_ratings: bool):
    try:
        with open("cache/credits_cache.json", "r") as f:
            credits_cache = json.load(f)
    except FileNotFoundError:
        credits_cache = {}

    try:
        with open("cache/ratings_cache.json", "r") as f:
            ratings_cache = json.load(f)
    except FileNotFoundError:
        ratings_cache = {}
    
    college_page_soup = get_soup(html)
    for subject_page_link in college_page_soup.find_all("a", href=lambda href: href and href.startswith("/webtms_du/courseList")):
        
        try:
            response = session.get(config.tms_base_url + subject_page_link["href"])
            response.raise_for_status()
            parsed_crns = parse_subject_page(response.text, data, include_ratings, ratings_cache)
        except Exception as e:
            raise Exception("Error scraping/parsing subject page: {}".format(subject_page_link["href"])) from e

        for crn, crn_page_link in parsed_crns.items():
            if crn in credits_cache:
                data[crn]["credits"] = credits_cache[crn]
            else:
                try:
                    response = session.get(config.tms_base_url + crn_page_link)
                    response.raise_for_status()
                    parse_crn_page(response.text, data)
                except Exception as e:
                    raise Exception("Error scraping/parsing CRN {}: {}".format(crn, crn_page_link)) from e
                credits_cache[crn] = data[crn]["credits"]

            print("Parsed CRN: " + crn + " (" + data[crn].get("course_title") + ")")
            print()

    if not os.path.exists("cache"):
        os.makedirs("cache")

    with open("cache/ratings_cache.json", "w") as f:
        json.dump(ratings_cache, f, indent=4)

    with open("cache/credits_cache.json", "w") as f:
        json.dump(credits_cache, f, indent=4)

    return data

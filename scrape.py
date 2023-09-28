from requests import Session
from bs4 import BeautifulSoup

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
    return session.get(config.get_college_page_url(college_code))


def scrape_all_subjects(session: Session, data: dict, html: str, include_ratings: bool):
    college_page_soup = get_soup(html)
    for subject_page_link in college_page_soup.find_all("a", href=lambda href: href and href.startswith("/webtms_du/courseList")):
        response = session.get(config.tms_base_url + subject_page_link["href"])
        parse_subject_page(response.text, data, include_ratings)

        subject_page_soup = get_soup(response.text)
        for crn_page_link in subject_page_soup.find_all("a", href=lambda href: href and href.startswith("/webtms_du/courseDetails")):
            response = session.get(config.tms_base_url + crn_page_link["href"])
            parse_crn_page(response.text, data)
    return data

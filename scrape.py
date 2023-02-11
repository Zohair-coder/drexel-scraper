from collections import defaultdict
from requests import Session
from bs4 import BeautifulSoup

from parse import parse
import config


def scrape(include_ratings: bool = False):
    session = Session()
    data = defaultdict(list)

    response = go_to_cci_page(session)
    parse_all_subjects(session, data, response.text, include_ratings)
    return data


def get_soup(html):
    return BeautifulSoup(html, "html.parser")


def go_to_cci_page(session: Session):
    return session.get(config.get_college_page_url(config.college))


def parse_all_subjects(session: Session, data: dict, html: str, include_ratings: bool):
    soup = get_soup(html)
    for link in soup.find_all("a", href=lambda href: href and href.startswith("/webtms_du/courseList")):
        response = session.get(config.tms_base_url + link["href"])
        parse(response.text, data, include_ratings)
    return data

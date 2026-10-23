from requests import Session, Response
from bs4 import BeautifulSoup
from cache_store import load_cache, save_cache
from typing import Any
import time
from urllib.parse import parse_qs, urlsplit
from terms import term_url, term_label
from helpers import send_request
from parse import parse_subject_page, parse_crn_page
import config
import login


def require_tms(response: Response) -> None:
    if urlsplit(response.url).hostname != "termmasterschedule.drexel.edu":
        raise ValueError("TMS session expired; retaining existing quarter")
    title = get_soup(response.text).title
    if title is None or "WebTMS" not in title.get_text():
        raise ValueError("Unexpected TMS response; refusing partial refresh")


def authenticated_session() -> Session:
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
    return session


def scrape(
    include_ratings: bool = False,
    all_colleges: bool = False,
    term_code: str | None = None,
    session: Session | None = None,
    term_index: int = 1,
    term_count: int = 1,
    term_name: str | None = None,
) -> dict[str, dict[str, Any]]:
    term_code = term_code or config.year + config.quarter
    session = session or authenticated_session()
    data: dict[str, dict[str, Any]] = {}

    if not all_colleges:
        college_codes = [config.college_code]
    else:
        college_codes = get_all_college_codes(session, term_code)

    for college_code in college_codes:
        response = go_to_college_page(session, college_code, term_code)
        require_tms(response)
        college_data: dict[str, dict[str, Any]] = {}
        scrape_all_subjects(
            session,
            college_data,
            response.text,
            include_ratings,
            term_code,
            term_index,
            term_count,
            term_name,
        )
        for course in college_data.values():
            course["college_code"] = college_code
        data.update(college_data)

    return data


def get_all_college_codes(session: Session, term_code: str) -> list[str]:
    response = send_request(session, term_url(term_code) + "?collCode=")
    require_tms(response)
    soup = get_soup(response.text)
    college_codes = []

    for link in soup.find_all(
        "a", href=lambda href: href and href.startswith("/webtms_du/collegesSubjects")
    ):
        code = parse_qs(urlsplit(str(link["href"])).query).get("collCode", [""])[0]
        if code and code not in college_codes:
            college_codes.append(code)

    if not college_codes:
        raise ValueError(f"No colleges found for {term_code}; refusing partial refresh")

    return college_codes


def get_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def go_to_college_page(session: Session, college_code: str, term_code: str) -> Response:
    return send_request(session, term_url(term_code) + "?collCode=" + college_code)


def scrape_all_subjects(
    session: Session,
    data: dict[str, dict[str, Any]],
    html: str,
    include_ratings: bool,
    term_code: str,
    term_index: int = 1,
    term_count: int = 1,
    term_name: str | None = None,
) -> dict[str, dict[str, Any]]:
    extra_course_data_cache = load_cache("cache/extra_course_data_cache.json")
    ratings_cache = load_cache("cache/ratings_cache.json")

    college_page_soup = get_soup(html)
    for subject_page_link in college_page_soup.find_all(
        "a", href=lambda href: href and href.startswith("/webtms_du/courseList")
    ):
        try:
            response = send_request(
                session, config.tms_base_url + subject_page_link["href"]
            )
            require_tms(response)
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
            cache_key = f"{term_code}:{crn}"
            if cache_key in extra_course_data_cache:
                data[crn]["credits"] = extra_course_data_cache[cache_key]["credits"]
                data[crn]["prereqs"] = extra_course_data_cache[cache_key]["prereqs"]
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

                extra_course_data_cache[cache_key] = {
                    "credits": data[crn]["credits"],
                    "prereqs": data[crn]["prereqs"],
                }

            print(
                f"Parsed CRN: {crn} ({data[crn]['course_title']}) "
                f"— {term_name or term_label(term_code)} ({term_code}) ({term_index}/{term_count})"
            )
            print()

    save_cache("cache/ratings_cache.json", ratings_cache)
    save_cache("cache/extra_course_data_cache.json", extra_course_data_cache)

    return data

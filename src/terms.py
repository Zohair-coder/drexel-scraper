"""Quarter discovery from TMS; calendar labels differ from academic term codes."""

import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

BASE = "https://termmasterschedule.drexel.edu/webtms_du"


def term_label(code: str) -> str:
    if not re.fullmatch(r"\d{4}(15|25|35|45)", code):
        raise ValueError(f"Invalid quarter code: {code}")
    season = {"15": "Fall", "25": "Winter", "35": "Spring", "45": "Summer"}[code[-2:]]
    year = int(code[:4]) + (code[-2:] != "15")
    return f"{season} {year}"


def term_url(code: str) -> str:
    term_label(code)
    return f"{BASE}/collegesSubjects/{code}"


def discover_terms(html: str) -> dict[str, str]:
    result = {}
    for link in BeautifulSoup(html, "html.parser").select("a[href]"):
        match = re.fullmatch(
            r"/webtms_du/collegesSubjects/(\d{4}(?:15|25|35|45))",
            urlsplit(str(link["href"])).path,
        )
        if match and "Quarter" in link.get_text():
            result[match[1]] = term_label(match[1])
    if not result:
        raise ValueError("No quarters in TMS catalogue; preserving stored availability")
    return result

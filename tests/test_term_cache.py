"""Term-specific credits/prerequisites must never leak through a reused CRN."""

import json
import os
from pathlib import Path
import sys

import pytest
from requests import Response

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.mark.parametrize("corrupt_cache", [False, True])
def test_cache_keys_and_session_expiry(tmp_path, monkeypatch, corrupt_cache):
    monkeypatch.setenv("DREXEL_EMAIL", "test@example.test")
    monkeypatch.setenv("DREXEL_PASSWORD", "test")
    import scrape

    monkeypatch.chdir(tmp_path)
    os.mkdir("cache")
    Path("cache/extra_course_data_cache.json").write_text(
        json.dumps(
            {
                "12345": {"credits": "legacy", "prereqs": "wrong"},
                "202615:12345": {"credits": "3", "prereqs": "fall"},
            }
        )
    )
    if corrupt_cache:
        Path("cache/extra_course_data_cache.json").write_text('{"interrupted":')
        Path("cache/ratings_cache.json").write_text("")
    response = Response()
    response.url = "https://termmasterschedule.drexel.edu/webtms_du/courseList/CS"
    response._content = b"<title>WebTMS - Courses</title>"
    calls = []

    def request(session, url):
        calls.append(url)
        return response

    def parse_subject(html, data, *args):
        data["12345"] = {"course_title": "Intro"}
        return {"12345": "/webtms_du/courseDetails/12345"}

    def parse_details(html, data):
        data["12345"].update(credits="4", prereqs="winter")

    monkeypatch.setattr(scrape, "send_request", request)
    monkeypatch.setattr(scrape, "parse_subject_page", parse_subject)
    monkeypatch.setattr(scrape, "parse_crn_page", parse_details)
    html = '<a href="/webtms_du/courseList/CS">CS</a>'
    data = {}
    scrape.scrape_all_subjects(None, data, html, False, "202625")
    assert data["12345"]["prereqs"] == "winter"
    assert len(calls) == 2
    calls.clear()
    scrape.scrape_all_subjects(None, data, html, False, "202615")
    assert data["12345"]["prereqs"] == ("winter" if corrupt_cache else "fall")
    assert len(calls) == (2 if corrupt_cache else 1)
    assert json.loads(Path("cache/ratings_cache.json").read_text()) == {}
    response.url = "https://connect.drexel.edu/login"
    with pytest.raises(ValueError, match="session expired"):
        scrape.require_tms(response)

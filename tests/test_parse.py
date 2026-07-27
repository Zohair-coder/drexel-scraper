"""Unit tests for schedule parsing helpers."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parse import UNSCHEDULED_VALUES, parse_days, parse_time


def test_unscheduled_values_contains_expected_markers() -> None:
    assert UNSCHEDULED_VALUES == {"", "TBD", "Asynchronous"}


@pytest.mark.parametrize("value", ["", "TBD", "Asynchronous"])
def test_parse_days_returns_none_for_unscheduled_values(value: str) -> None:
    assert parse_days(value) is None


def test_parse_days_expands_day_codes() -> None:
    assert parse_days("MWF") == ["Monday", "Wednesday", "Friday"]


@pytest.mark.parametrize(
    "code,expected",
    [
        ("M", ["Monday"]),
        ("T", ["Tuesday"]),
        ("W", ["Wednesday"]),
        ("R", ["Thursday"]),
        ("F", ["Friday"]),
        ("S", ["Saturday"]),
        ("U", ["Sunday"]),
    ],
)
def test_parse_days_single_day_codes(code: str, expected: list[str]) -> None:
    assert parse_days(code) == expected


def test_parse_days_handles_full_week() -> None:
    assert parse_days("MTWRFSU") == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]


def test_parse_days_raises_key_error_for_unknown_day_code() -> None:
    with pytest.raises(KeyError):
        parse_days("X")


@pytest.mark.parametrize("value", ["", "TBD", "Asynchronous"])
def test_parse_time_returns_none_for_unscheduled_values(value: str) -> None:
    assert parse_time(value) == (None, None)


def test_parse_time_converts_range_to_24_hour_time() -> None:
    assert parse_time("10:00 AM - 12:30 PM") == ("10:00", "12:30")


def test_parse_time_handles_single_digit_hour() -> None:
    assert parse_time("9:00 AM - 9:50 AM") == ("09:00", "09:50")


def test_parse_time_handles_noon_boundary() -> None:
    assert parse_time("12:00 PM - 1:00 PM") == ("12:00", "13:00")


def test_parse_time_handles_midnight_boundary() -> None:
    assert parse_time("12:00 AM - 1:00 AM") == ("00:00", "01:00")


def test_parse_time_raises_value_error_for_malformed_range() -> None:
    with pytest.raises(ValueError):
        parse_time("10:00 AM")

"""Unit tests for schedule parsing helpers."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parse import parse_days, parse_time


@pytest.mark.parametrize("value", ["", "TBD", "Asynchronous"])
def test_parse_days_returns_none_for_unscheduled_values(value: str) -> None:
    assert parse_days(value) is None


def test_parse_days_expands_day_codes() -> None:
    assert parse_days("MWF") == ["Monday", "Wednesday", "Friday"]


@pytest.mark.parametrize("value", ["", "TBD", "Asynchronous"])
def test_parse_time_returns_none_for_unscheduled_values(value: str) -> None:
    assert parse_time(value) == (None, None)


def test_parse_time_converts_range_to_24_hour_time() -> None:
    assert parse_time("10:00 AM - 12:30 PM") == ("10:00", "12:30")

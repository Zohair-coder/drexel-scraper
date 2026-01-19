"""Unit tests for quarter_utils module."""

import pytest
from datetime import datetime
from unittest.mock import patch

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from quarter_utils import get_current_quarter_and_year, get_quarter_name


class TestGetCurrentQuarterAndYear:
    """Tests for get_current_quarter_and_year function."""

    @pytest.mark.parametrize(
        "date,expected_year,expected_quarter,description",
        [
            # Fall quarter (July 1 - September 27)
            ((2025, 7, 1), "2025", "15", "Fall start - July 1"),
            ((2025, 8, 15), "2025", "15", "Fall middle - August"),
            ((2025, 9, 27), "2025", "15", "Fall end - September 27"),
            # Winter quarter (September 28 - January 15)
            ((2025, 9, 28), "2025", "25", "Winter start - September 28"),
            ((2025, 10, 15), "2025", "25", "Winter - October"),
            ((2025, 11, 15), "2025", "25", "Winter - November"),
            ((2025, 12, 15), "2025", "25", "Winter - December"),
            ((2026, 1, 10), "2025", "25", "Winter - January (year rollback)"),
            ((2026, 1, 15), "2025", "25", "Winter end - January 15"),
            # Spring quarter (January 16 - April 14)
            ((2026, 1, 16), "2025", "35", "Spring start - January 16"),
            ((2026, 2, 15), "2025", "35", "Spring - February"),
            ((2026, 3, 15), "2025", "35", "Spring - March"),
            ((2026, 4, 14), "2025", "35", "Spring end - April 14"),
            # Summer quarter (April 15 - June 30)
            ((2026, 4, 15), "2025", "45", "Summer start - April 15"),
            ((2026, 5, 15), "2025", "45", "Summer - May"),
            ((2026, 6, 15), "2025", "45", "Summer - June"),
            ((2026, 6, 30), "2025", "45", "Summer end - June 30"),
            # Different academic years
            ((2024, 7, 1), "2024", "15", "Fall 2024"),
            ((2025, 1, 20), "2024", "35", "Spring 2024-25"),
            ((2025, 5, 1), "2024", "45", "Summer 2024-25"),
        ],
    )
    def test_quarter_detection(
        self, date, expected_year, expected_quarter, description
    ):
        """Test that quarters are correctly detected from dates."""
        mock_datetime = datetime(*date)
        with patch("quarter_utils.datetime") as mock_dt:
            mock_dt.now.return_value = mock_datetime
            year, quarter = get_current_quarter_and_year()
            assert (
                year == expected_year
            ), f"{description}: expected year {expected_year}, got {year}"
            assert (
                quarter == expected_quarter
            ), f"{description}: expected quarter {expected_quarter}, got {quarter}"

    def test_quarter_code_format(self):
        """Test that quarter codes are in expected format."""
        with patch("quarter_utils.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 10, 1)
            year, quarter = get_current_quarter_and_year()
            # Year should be 4-digit string
            assert len(year) == 4
            assert year.isdigit()
            # Quarter should be 2-digit string
            assert len(quarter) == 2
            assert quarter.isdigit()
            # Combined code should be 6 digits
            assert len(year + quarter) == 6


class TestGetQuarterName:
    """Tests for get_quarter_name function."""

    @pytest.mark.parametrize(
        "code,expected_name",
        [
            ("15", "Fall"),
            ("25", "Winter"),
            ("35", "Spring"),
            ("45", "Summer"),
        ],
    )
    def test_valid_quarter_codes(self, code, expected_name):
        """Test that valid quarter codes return correct names."""
        assert get_quarter_name(code) == expected_name

    def test_invalid_quarter_code(self):
        """Test that invalid quarter codes return 'Unknown'."""
        assert get_quarter_name("00") == "Unknown"
        assert get_quarter_name("99") == "Unknown"
        assert get_quarter_name("") == "Unknown"


class TestAcademicYearBoundaries:
    """Tests for academic year boundary handling."""

    def test_winter_january_uses_previous_year(self):
        """Winter quarter in January should use previous calendar year."""
        with patch("quarter_utils.datetime") as mock_dt:
            # January 10, 2026 should be Winter 2025 (202525)
            mock_dt.now.return_value = datetime(2026, 1, 10)
            year, quarter = get_current_quarter_and_year()
            assert year == "2025"
            assert quarter == "25"

    def test_spring_uses_previous_year(self):
        """Spring quarter should use previous calendar year."""
        with patch("quarter_utils.datetime") as mock_dt:
            # March 2026 should be Spring 2025 (202535)
            mock_dt.now.return_value = datetime(2026, 3, 15)
            year, quarter = get_current_quarter_and_year()
            assert year == "2025"
            assert quarter == "35"

    def test_summer_uses_previous_year(self):
        """Summer quarter should use previous calendar year."""
        with patch("quarter_utils.datetime") as mock_dt:
            # June 2026 should be Summer 2025 (202545)
            mock_dt.now.return_value = datetime(2026, 6, 15)
            year, quarter = get_current_quarter_and_year()
            assert year == "2025"
            assert quarter == "45"

    def test_fall_uses_current_year(self):
        """Fall quarter should use current calendar year."""
        with patch("quarter_utils.datetime") as mock_dt:
            # August 2026 should be Fall 2026 (202615)
            mock_dt.now.return_value = datetime(2026, 8, 15)
            year, quarter = get_current_quarter_and_year()
            assert year == "2026"
            assert quarter == "15"

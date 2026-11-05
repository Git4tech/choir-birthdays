from datetime import date

import pytest

from birthdays.sheet import parse_dob

MAY_14 = date(2000, 5, 14)


@pytest.mark.parametrize(
    "raw",
    ["14/05", "14-05", "14.05", "14 May", "14 de maio", "May 14", "2001-05-14", "14/05/1990", "05/14"],
)
def test_parse_dob_layouts(raw):
    assert parse_dob(raw) == MAY_14


def test_parse_dob_sheets_serial_number():
    serial = (date(2026, 5, 14) - date(1899, 12, 30)).days
    assert parse_dob(serial) == MAY_14


def test_parse_dob_leap_day():
    assert parse_dob("29/02") == date(2000, 2, 29)


@pytest.mark.parametrize("raw", ["", "hello", "31/02", "32/13"])
def test_parse_dob_rejects_nonsense(raw):
    assert parse_dob(raw) is None
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from birthdays.models import Base, Member, Unit
from birthdays.reminders import birthday_this_year, birthdays_on


def test_normal_birthday():
    assert birthday_this_year(date(1990, 5, 14), 2026) == date(2026, 5, 14)


def test_leap_day_non_leap_year():
    assert birthday_this_year(date(2000, 2, 29), 2026) == date(2026, 2, 28)


def test_leap_day_leap_year():
    assert birthday_this_year(date(2000, 2, 29), 2028) == date(2028, 2, 29)


def test_birthdays_on():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        unit = Unit(name="Choir")
        s.add(unit)
        s.flush()
        s.add_all([
            Member(unit_id=unit.id, name="Ada", date_of_birth=date(1990, 5, 14)),
            Member(unit_id=unit.id, name="Bo", date_of_birth=date(1985, 6, 1)),
        ])
        s.commit()
        assert list(birthdays_on(s, date(2026, 5, 14)).values()) == [["Ada"]]
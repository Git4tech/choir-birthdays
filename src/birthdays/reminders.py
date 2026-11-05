from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import config
from .models import Member, ReminderLog, Unit
from .notifiers import get_notifier


def birthday_this_year(dob: date, year: int) -> date:
    try:
        return dob.replace(year=year)
    except ValueError:               # 29 Feb in a non-leap year -> 28 Feb
        return date(year, 2, 28)


def birthdays_on(session: Session, day: date) -> dict[Unit, list[str]]:
    rows = session.execute(
        select(Member, Unit).join(Unit, Member.unit_id == Unit.id).where(Member.active.is_(True))
    ).all()
    result: dict[Unit, list[str]] = {}
    for member, unit in rows:
        if birthday_this_year(member.date_of_birth, day.year) == day:
            result.setdefault(unit, []).append(member.name)
    return {unit: sorted(names) for unit, names in result.items()}


def build_message(unit_name: str, names: list[str]) -> str:
    bullets = "\n".join(f"• {n}" for n in names)
    return f"🎂 Birthday reminder – {unit_name}\n{bullets}"


def run_reminders(session: Session, *, dry_run: bool = False, force: bool = False) -> tuple[int, int]:
    now = datetime.now(ZoneInfo(config.TIMEZONE))
    if not force and now.hour < config.SEND_AFTER_HOUR:
        print(f"Too early ({now:%H:%M} {config.TIMEZONE}); waiting for {config.SEND_AFTER_HOUR}:00.")
        return 0, 0

    today = now.date()
    notifier = get_notifier()
    sent = failed = 0

    for unit, names in birthdays_on(session, today).items():
        message = build_message(unit.name, names)
        if dry_run:
            print(message)
            continue

        log = session.scalar(
            select(ReminderLog).where(
                ReminderLog.unit_id == unit.id,
                ReminderLog.reminder_date == today,
                ReminderLog.channel == notifier.name,
            )
        )
        if log and log.status == "sent":
            print(f"Already sent today for {unit.name}.")
            continue

        # Any send failure must be logged as "failed", never crash the whole run.
        try:
            notifier.send(message)
            status, detail = "sent", None
        except Exception as exc:  # noqa: BLE001
            status, detail = "failed", str(exc)[:500]

        if log is None:
            log = ReminderLog(unit_id=unit.id, reminder_date=today, channel=notifier.name)
            session.add(log)
        log.status, log.detail = status, detail
        log.sent_at = datetime.now(UTC)
        session.commit()                       # record it immediately

        print(f"{unit.name}: {status}")
        if status == "sent":
            sent += 1
        else:
            failed += 1
    return sent, failed
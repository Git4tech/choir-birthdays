from sqlalchemy import select
from sqlalchemy.orm import Session

from . import sheet
from .models import Member, Unit


def sync_from_sheet(session: Session) -> dict[str, int]:
    stats = {"added": 0, "updated": 0, "deactivated": 0}
    for unit_name, people in sheet.read_units().items():
        unit = session.scalar(select(Unit).where(Unit.name == unit_name))
        if unit is None:
            unit = Unit(name=unit_name)
            session.add(unit)
            session.flush()

        existing = {m.name: m for m in session.scalars(select(Member).where(Member.unit_id == unit.id))}
        if not people and existing:
            print(f"[warn] '{unit_name}' came back empty, so I'm leaving its members unchanged")
            continue

        seen: set[str] = set()
        for name, dob in people:
            if name in seen:
                print(f"[warn] duplicate name '{name}' in '{unit_name}', skipped")
                continue
            seen.add(name)
            member = existing.get(name)
            if member is None:
                session.add(Member(unit_id=unit.id, name=name, date_of_birth=dob))
                stats["added"] += 1
            elif member.date_of_birth != dob or not member.active:
                member.date_of_birth, member.active = dob, True
                stats["updated"] += 1

        for name, member in existing.items():            # removed from the sheet
            if name not in seen and member.active:
                member.active = False
                stats["deactivated"] += 1
    return stats
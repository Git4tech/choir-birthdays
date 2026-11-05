from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Unit(Base):
    __tablename__ = "units"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("unit_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    name: Mapped[str] = mapped_column(String(200))
    date_of_birth: Mapped[date] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ReminderLog(Base):
    """One row per unit per day per channel. This is what makes reruns safe."""
    __tablename__ = "reminder_log"
    __table_args__ = (UniqueConstraint("unit_id", "reminder_date", "channel"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    reminder_date: Mapped[date] = mapped_column(Date)
    channel: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20))        # sent / failed
    detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
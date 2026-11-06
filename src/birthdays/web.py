from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from sqlalchemy import select

from birthdays import config
from birthdays.db import session_scope
from birthdays.models import Member, ReminderLog, Unit
from birthdays.reminders import birthday_this_year

st.set_page_config(page_title="Choir Birthdays", page_icon="🎂")
st.title("🎂 Choir Birthdays")

today = datetime.now(ZoneInfo(config.TIMEZONE)).date()


def next_birthday(dob: date) -> date:
    this_year = birthday_this_year(dob, today.year)
    return this_year if this_year >= today else birthday_this_year(dob, today.year + 1)


@st.cache_data(ttl=300)
def load_members() -> pd.DataFrame:
    with session_scope() as s:
        rows = s.execute(
            select(Member.name, Unit.name, Member.date_of_birth)
            .join(Unit, Member.unit_id == Unit.id)
            .where(Member.active.is_(True))
        ).all()
    df = pd.DataFrame(rows, columns=["Name", "Unit", "Date of birth"])
    df["Next birthday"] = df["Date of birth"].map(next_birthday)
    df["In (days)"] = df["Next birthday"].map(lambda d: (d - today).days)
    return df.sort_values("In (days)")


@st.cache_data(ttl=300)
def load_log() -> pd.DataFrame:
    with session_scope() as s:
        rows = s.execute(
            select(ReminderLog.sent_at, Unit.name, ReminderLog.channel,
                   ReminderLog.status, ReminderLog.detail)
            .join(Unit, ReminderLog.unit_id == Unit.id)
            .order_by(ReminderLog.sent_at.desc())
            .limit(50)
        ).all()
    return pd.DataFrame(rows, columns=["Sent at", "Unit", "Channel", "Status", "Detail"])


members = load_members()
choice = st.selectbox("Unit", ["All units", *sorted(members["Unit"].unique())])
if choice != "All units":
    members = members[members["Unit"] == choice]

columns = ["Name", "Unit", "Next birthday", "In (days)"]
tab_today, tab_soon, tab_all, tab_log = st.tabs(["Today", "Next 30 days", "Everyone", "Reminder log"])

with tab_today:
    todays = members[members["In (days)"] == 0]
    if todays.empty:
        st.info("No birthdays today.")
    for _, row in todays.iterrows():
        st.success(f"🎉 {row['Name']} ({row['Unit']})")

with tab_soon:
    st.dataframe(members[members["In (days)"] <= 30][columns], hide_index=True)

with tab_all:
    st.dataframe(members[columns], hide_index=True)

with tab_log:
    st.dataframe(load_log(), hide_index=True)
import json
import re
from datetime import date, timedelta

import gspread
from google.oauth2.service_account import Credentials

from . import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Only the day and month matter. Everyone is stored with this placeholder year
# (a leap year, so 29 Feb stays valid). Any birth year in the Sheet is ignored.
PLACEHOLDER_YEAR = 2000

DOB_HEADERS = ("date_of_birth", "dob", "birthday", "birthdate", "date")

MONTHS = {
    "jan": 1, "janeiro": 1, "january": 1,
    "fev": 2, "feb": 2, "fevereiro": 2, "february": 2,
    "mar": 3, "marco": 3, "março": 3, "march": 3,
    "abr": 4, "apr": 4, "abril": 4, "april": 4,
    "mai": 5, "may": 5, "maio": 5,
    "jun": 6, "junho": 6, "june": 6,
    "jul": 7, "julho": 7, "july": 7,
    "ago": 8, "aug": 8, "agosto": 8, "august": 8,
    "set": 9, "sep": 9, "sept": 9, "setembro": 9, "september": 9,
    "out": 10, "oct": 10, "outubro": 10, "october": 10,
    "nov": 11, "novembro": 11, "november": 11,
    "dez": 12, "dec": 12, "dezembro": 12, "december": 12,
}

ISO_DATE = re.compile(r"\d{4}-(\d{1,2})-(\d{1,2})")                         # 2000-05-14
NUMERIC_DATE = re.compile(r"(\d{1,2})[/\-.](\d{1,2})(?:[/\-.]\d{2,4})?")    # 14/05, 14/05/1990
DAY_MONTH_NAME = re.compile(
    r"(\d{1,2})(?:\s+de)?[\s\-./]*([a-zç]+)\.?(?:[\s\-./,]*(?:de\s+)?\d{2,4})?"
)                                                                           # 14 May, 14 de maio
MONTH_NAME_DAY = re.compile(r"([a-zç]+)\.?[\s\-./]*(\d{1,2})(?:[\s\-./,]+\d{2,4})?")   # May 14


def _client() -> gspread.Client:
    if config.GOOGLE_CREDENTIALS_JSON:            # GitHub Actions: JSON in a secret
        info = json.loads(config.GOOGLE_CREDENTIALS_JSON)
    else:                                          # local: JSON file
        with open(config.GOOGLE_CREDENTIALS_FILE, encoding="utf-8") as f:
            info = json.load(f)
    return gspread.authorize(Credentials.from_service_account_info(info, scopes=SCOPES))


def _make_date(month: int, day: int) -> date | None:
    try:
        return date(PLACEHOLDER_YEAR, month, day)
    except ValueError:
        return None


def parse_dob(raw) -> date | None:
    """Read a day and month from 14/05, 14-05, 14 May, 14 de maio, May 14,
    2000-05-14, 14/05/1990 or a Sheets date serial number. Day-first is assumed."""
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        d = date(1899, 12, 30) + timedelta(days=int(raw))       # Sheets date serial
        return _make_date(d.month, d.day)

    text = str(raw).strip().lower()
    if m := ISO_DATE.fullmatch(text):
        return _make_date(int(m[1]), int(m[2]))
    if m := NUMERIC_DATE.fullmatch(text):
        a, b = int(m[1]), int(m[2])
        return _make_date(b, a) or _make_date(a, b)             # day first, else month first
    if (m := DAY_MONTH_NAME.fullmatch(text)) and m[2] in MONTHS:
        return _make_date(MONTHS[m[2]], int(m[1]))
    if (m := MONTH_NAME_DAY.fullmatch(text)) and m[1] in MONTHS:
        return _make_date(MONTHS[m[1]], int(m[2]))
    return None


def _norm(key) -> str:
    return re.sub(r"[\s\-]+", "_", str(key).strip().lower())


def read_units() -> dict[str, list[tuple[str, date]]]:
    """Return {unit name: [(person name, birthday), ...]}, one worksheet per unit."""
    book = _client().open_by_key(config.SPREADSHEET_ID)
    units: dict[str, list[tuple[str, date]]] = {}
    for ws in book.worksheets():
        if ws.title.startswith("_"):
            continue
        records = ws.get_all_records(
            value_render_option="UNFORMATTED_VALUE",
            numericise_ignore=["all"],
        )
        people = []
        for record in records:
            row = {_norm(k): v for k, v in record.items()}
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            raw = next((row[h] for h in DOB_HEADERS if row.get(h) not in (None, "")), "")
            dob = parse_dob(raw)
            if dob is None:
                print(f"[warn] {ws.title}: can't read the birthday for '{name}' (got {raw!r})")
                continue
            people.append((name, dob))
        units[ws.title.strip()] = people
    return units
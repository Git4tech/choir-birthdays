import os

from dotenv import load_dotenv

load_dotenv()


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "sqlite:///birthdays.db")
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return url.replace(prefix, "postgresql+psycopg://", 1)
    return url


DATABASE_URL = _db_url()
TIMEZONE = os.environ.get("APP_TIMEZONE", "Europe/Lisbon")
SEND_AFTER_HOUR = int(os.environ.get("SEND_AFTER_HOUR", "8"))
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_CREDENTIALS_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
NOTIFIER = os.environ.get("NOTIFIER", "console")
CALLMEBOT_PHONE = os.environ.get("CALLMEBOT_PHONE", "")
CALLMEBOT_APIKEY = os.environ.get("CALLMEBOT_APIKEY", "")
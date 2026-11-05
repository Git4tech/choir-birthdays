# cli.py
import argparse

from . import __version__
from .db import session_scope
from .reminders import run_reminders
from .sync import sync_from_sheet


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="birthdays")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync", help="copy the Google Sheet into the database")
    remind = sub.add_parser("remind", help="send today's reminders")
    remind.add_argument("--dry-run", action="store_true", help="print, don't send")
    remind.add_argument("--force", action="store_true", help="ignore the 8am rule")
    args = parser.parse_args(argv)

    with session_scope() as session:
        if args.cmd == "sync":
            print(sync_from_sheet(session))
            return 0
        _, failed = run_reminders(session, dry_run=args.dry_run, force=args.force)
        return 1 if failed else 0     # non-zero makes GitHub email you about the failure
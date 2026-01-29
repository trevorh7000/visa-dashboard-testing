import argparse
import sqlite3
import os
from datetime import datetime, timezone, timedelta
import sys

# ---- Database path (canonical) ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "visa-dashboard-web", "decisions.db")

# ---- DB helpers ----

def connect():
    return sqlite3.connect(DB_PATH)

def list_settings():
    with connect() as conn:
        rows = conn.execute(
            "SELECT setting, value FROM settings ORDER BY setting"
        ).fetchall()

    if not rows:
        print("(settings table empty)")
        return

    for key, value in rows:
        print(f"{key}: {value}")

def get_setting(key):
    with connect() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE setting = ?",
            (key,)
        ).fetchone()

    # print(row[0] if row else "(not set)") # not needed now as ai return the values
    return row[0] if row else None

def set_setting(key, value):
    with connect() as conn:
        conn.execute("""
            INSERT INTO settings (setting, value)
            VALUES (?, ?)
            ON CONFLICT(setting) DO UPDATE SET value=excluded.value
        """, (key, value))

def delete_setting(key):
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM settings WHERE setting = ?",
            (key,)
        )
        if cur.rowcount == 0:
            print(f"{key} not found")
        else:
            print(f"{key} deleted")

def reset_settings():
    confirm = input(
        "This will DELETE ALL rows in settings. Type 'yes' to continue: "
    ).strip().lower()

    if confirm != "yes":
        print("Reset aborted")
        sys.exit(1)

    with connect() as conn:
        conn.execute("DELETE FROM settings")

    print("settings table cleared")

def get_scraped_files():
    with connect() as conn:
        rows = conn.execute(
            "SELECT filename, url, date_added FROM scraped_files ORDER BY date_added DESC"
        ).fetchall()
    return rows

# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(
        description="Helper utility for decisions.db settings"
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-l", "--list",
        action="store_true",
        help="List all settings"
    )

    group.add_argument(
        "--get",
        metavar="KEY",
        help="Get a setting value"
    )

    group.add_argument(
        "--set",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="Set a setting value (use 't' for current UTC time or 'to' for 24 hours ago" \
        ")"
    )

    group.add_argument(
        "--unset",
        metavar="KEY",
        help="Set a setting value to NULL"
    )

    group.add_argument(
        "--del",
        dest="delete",
        metavar="KEY",
        help="Delete a setting row entirely"
    )

    group.add_argument(
        "-r", "--reset",
        action="store_true",
        help="Delete all rows from settings (requires confirmation)"
    )

    args = parser.parse_args()

    if args.list:
        list_settings()

    elif args.get:
        get_setting(args.get)

    elif args.set:
        key, value = args.set

        if value.lower() == "t":
            value = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if value.lower() == "to":
            value = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")

        set_setting(key, value)
        print(f"{key} set to {value}")

    elif args.unset:
        set_setting(args.unset, None)
        print(f"{args.unset} unset (NULL)")

    elif args.delete:
        delete_setting(args.delete)

    elif args.reset:
        reset_settings()

if __name__ == "__main__":
    main()

# CREATE TABLE scraped_files (
#     filename TEXT PRIMARY KEY,
#     url TEXT,
#     date_added TEXT
# );

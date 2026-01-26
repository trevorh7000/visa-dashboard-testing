#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processor for South Africa Visa Desk PDF data.
This script processes downloaded PDFs, extracts data, and updates
the Streamlit dashboard with new records.
"""

import os
import re
import sqlite3
import shutil
import pdfplumber
from datetime import datetime, date
import subprocess

import logging
logger = logging.getLogger(__name__)

# === wrapping: moved global setup into a function
def setup():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    to_process_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "pdf", "to_process"))
    processed_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "pdf", "processed"))
    app_path = os.path.join(script_dir, "..", "visa-dashboard-web") 
    db_path = os.path.join(app_path, "decisions.db")
    message_file = os.path.join(app_path, "message.txt")
    
    os.makedirs(to_process_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    # Clear message file
    with open(message_file, "w") as f:
        pass

    return to_process_dir, processed_dir, app_path, db_path, message_file
# === end wrapping


# === Write Message ===
def write_message(message, message_file):
    with open(message_file, "a") as f:
        f.write(message)

# === DATABASE SETUP ===
def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_number TEXT NOT NULL,
            decision TEXT NOT NULL,
            week TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL, 
            filename TEXT NOT NULL,
            date_added TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(app_number, week)
        )
    """)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS settings (
        setting TEXT PRIMARY KEY,
        value TEXT NOT NULL
)
''')
    conn.commit()
    return conn


# === FILENAME PARSING ===
def extract_week_label(filename, today=None):
    if today is None:
        today = date.today()

    # With year explicitly in the filename
    match_with_year = re.search(r"SAVD-Decisions-(\d{1,2})-([A-Za-z]+)-to-(\d{1,2})-([A-Za-z]+)-(\d{4})", filename)
    if match_with_year:
        d1, m1, d2, m2, y = match_with_year.groups()
        start_date = datetime.strptime(f"{d1}-{m1}-{y}", "%d-%B-%Y").date()
        end_date = datetime.strptime(f"{d2}-{m2}-{y}", "%d-%B-%Y").date()
        week_label = f"{start_date.strftime('%d %b')} to {end_date.strftime('%d %b %Y')}"
        return week_label, start_date, end_date

    # Without year in the filename — infer the year
    match_without_year = re.search(r"SAVD-Decisions-(\d{1,2})-([A-Za-z]+)-to-(\d{1,2})-([A-Za-z]+)", filename)
    if match_without_year:
        d1, m1, d2, m2 = match_without_year.groups()

        try:
            end_try = datetime.strptime(f"{d2}-{m2}-{today.year}", "%d-%B-%Y").date()
        except ValueError:
            return None, None, "Invalid-Date"

        if end_try > today:
            year = today.year - 1
        else:
            year = today.year

        start_date = datetime.strptime(f"{d1}-{m1}-{year}", "%d-%B-%Y").date()
        end_date = datetime.strptime(f"{d2}-{m2}-{year}", "%d-%B-%Y").date()

        if end_date < start_date:
            end_date = end_date.replace(year=year + 1)

        week_label = f"{start_date.strftime('%d %b')} to {end_date.strftime('%d %b %Y')}"
        return  week_label, start_date, end_date
    return None, None, "Unknown-Week"

# === PDF PARSING ===
def process_pdf(filepath, week_label, message_file):
    rows = []
    with pdfplumber.open(filepath) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            table = page.extract_table()
            print(f"Page {page_number}: table found = {bool(table)}")
            if not table:
                continue
            for row in table:
                if "Application Number" in row[0] or "Decision" in row[1]:
                    continue
                if row[0] and row[1]:
                    rows.append([row[0].strip(), row[1].strip()])
    text_to_go = f"Extracted {len(rows)} rows from {os.path.basename(filepath)}"
    print(text_to_go)
    write_message(text_to_go, message_file)
    return rows

# === DATABASE INSERT ===
def insert_into_db(conn, rows, week, start_date, end_date, filename, message_file):
    cur = conn.cursor()
    new_rows = 0
    for row in rows:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO decisions (app_number, decision, week, start_date, end_date, filename)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (row[0], row[1], week, start_date, end_date, filename))
            if cur.rowcount > 0:
                new_rows += 1
        except Exception as e:
            print(f"Error inserting row: {row} | {e}")
    conn.commit()
    text_to_go = f"Inserted {new_rows} new records."
    print(text_to_go)
    write_message(' - ' + text_to_go + '\n', message_file)
    return new_rows

# === STREAMLIT UPDATE ROUTINE ===
def update_dashboard(app_path):
    dashboard_path = os.path.join(app_path, "dashboard.py")
    with open(dashboard_path, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.strip().startswith("# cache-bust"):
            lines[i] = f"# cache-bust: {datetime.now().isoformat()}\n"
            break

    with open(dashboard_path, "w") as f:
        f.writelines(lines)

    print("✅ Updated dashboard.py with new cache-bust comment.")
    logger.info("Updated dashboard.py with new cache-bust comment.")

# === GIT COMMIT & PUSH ===
# === GIT COMMIT & PUSH ===
def commit_and_push_updates(app_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"Auto update from processor script @ {timestamp}"
    files = ["dashboard.py", "decisions.db", "message.txt"]

    try:
        for fname in files:
            subprocess.run(["git", "add", fname], cwd=app_path, check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=app_path, check=True)
        subprocess.run(["git", "push"], cwd=app_path, check=True)
        print(f"✅ Git commit and push complete: {commit_msg}")
        logger.info(f"Git commit and push complete: {commit_msg}")
    except subprocess.CalledProcessError as e:
        print("❌ Git operation failed:", e)
        logger.error(f"Git operation failed: {e}")

def update_streamlit_data(app_path):
    update_dashboard(app_path)
    commit_and_push_updates(app_path)

# === wrapping: clean entry point function
def run_processor():
    to_process_dir, processed_dir, app_path, db_path, message_file = setup()
    total_new_rows = 0
    files = [f for f in os.listdir(to_process_dir) if f.lower().endswith(".pdf")]
    if not files:
        print("No PDFs to process.")
        logger.info("No PDFs to process.")
        return 0

    conn = init_db(db_path)

    for filename in files:
        filepath = os.path.join(to_process_dir, filename)
        print(f"\nProcessing {filename}")
        week_label, start_date, end_date = extract_week_label(filename)
        rows = process_pdf(filepath, week_label, message_file)
        inserted_rows = insert_into_db(conn, rows, week_label, start_date, end_date, filename, message_file)
        total_new_rows += inserted_rows

        dest_path = os.path.join(processed_dir, filename)
        shutil.move(filepath, dest_path)
        print(f"Moved to processed: {filename}")

    print("\nDone. All PDFs processed.")

    if total_new_rows > 0:
        write_message(f"Total new records inserted: {total_new_rows}\n", message_file)
        print(f"Total new records inserted: {total_new_rows}")
        logger.info(f"Total new records inserted: {total_new_rows}")
        update_streamlit_data(app_path)
        print("Streamlit data updated.")
    else:
        write_message("No new records inserted.\n", message_file)
        print("No new records inserted.")
        logger.info("No new records inserted.")

    
    return total_new_rows
# === end wrapping

# === safe CLI entry
if __name__ == "__main__":
    print ("Starting processor script...",datetime.now().isoformat())
    run_processor()
# === end wrapping

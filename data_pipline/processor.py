import os
import re
import csv
import pdfplumber
import sqlite3
from datetime import datetime

# === FOLDER SETUP ===
PDF_DIR = os.path.expanduser("~/Documents/FGW/pdf")  # where PDFs and new_pdfs.txt are
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # location of this script
DB_PATH = os.path.join(SCRIPT_DIR, "decisions.db")
NEW_LIST_FILE = os.path.join(PDF_DIR, "new_pdfs.txt")


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
            filename TEXT NOT NULL,
            date_added TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(app_number, week)
        )
    """)
    conn.commit()
    return conn


# === FILENAME PARSING ===
def extract_week_label(filename):
    # Match things like SAVD-Decisions-24-June-to-30-June-2025.pdf
    match = re.search(r"SAVD-Decisions-(\d{1,2}-[A-Za-z]+)-to-(\d{1,2}-[A-Za-z]+-\d{4})", filename)
    if match:
        start, end = match.groups()
        return f"{start}-to-{end}"
    return "Unknown-Week"


# === PDF PARSING ===
def process_pdf(filepath, week_label):
    rows = []
    with pdfplumber.open(filepath) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            table = page.extract_table()
            print(f"Page {page_number}: table found = {bool(table)}")
            if not table:
                continue
            for row in table:
                # Skip headers
                if "Application Number" in row[0] or "Decision" in row[1]:
                    continue
                if row[0] and row[1]:
                    rows.append([row[0].strip(), row[1].strip()])
    print(f"Extracted {len(rows)} rows from {os.path.basename(filepath)}")
    return rows


# === DATABASE INSERT ===
def insert_into_db(conn, rows, week, filename):
    cur = conn.cursor()
    new_rows = 0
    for row in rows:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO decisions (app_number, decision, week, filename)
                VALUES (?, ?, ?, ?)
            """, (row[0], row[1], week, filename))
            if cur.rowcount > 0:
                new_rows += 1
        except Exception as e:
            print(f"Error inserting row: {row} | {e}")
    conn.commit()
    print(f"Inserted {new_rows} new records.")


# === MAIN LOGIC ===
def main():
    if not os.path.exists(NEW_LIST_FILE):
        print("No new_pdfs.txt file found.")
        return

    with open(NEW_LIST_FILE, "r") as f:
        pending_urls = [line.strip() for line in f if line.strip()]

    if not pending_urls:
        print("No new PDFs listed.")
        return

    conn = init_db(DB_PATH)

    for url in pending_urls[:]:  # work on a copy for safe removal
        filename = os.path.basename(url)
        filepath = os.path.join(PDF_DIR, filename)

        if not os.path.exists(filepath):
            print(f"Missing local file, skipping: {filename}")
            continue

        print(f"\nProcessing {filename}")
        week_label = extract_week_label(filename)
        rows = process_pdf(filepath, week_label)
        insert_into_db(conn, rows, week_label, filename)

        # Remove processed entry from list
        pending_urls.remove(url)
        with open(NEW_LIST_FILE, "w") as f:
            for remaining in pending_urls:
                f.write(remaining + "\n")

    print("\nDone. All new PDFs processed.")


if __name__ == "__main__":
    main()

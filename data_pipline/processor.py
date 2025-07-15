import os
import re
import sqlite3
import shutil
import pdfplumber
import re

# === FOLDER SETUP ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TO_PROCESS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "pdf", "to_process"))
PROCESSED_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "pdf", "processed"))
APP_PATH = os.path.join(SCRIPT_DIR, "..", "visa-dashboard-web") 
DB_PATH = os.path.join(APP_PATH, "decisions.db")
MESSAGE_FILE = os.path.join(APP_PATH, "message.txt")

# clearing out messgae.tx at start
with open(MESSAGE_FILE, "w") as f:
    pass  # This will clear the file if it exists, or create it if not


# === Write Message ===
def write_message(message):
    with open(MESSAGE_FILE, "a") as f:
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
            filename TEXT NOT NULL,
            date_added TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(app_number, week)
        )
    """)
    conn.commit()
    return conn


# === FILENAME PARSING ===


def extract_week_label(filename):
    # Match with year at the end
    match_with_year = re.search(r"SAVD-Decisions-(\d{1,2}-[A-Za-z]+)-to-(\d{1,2}-[A-Za-z]+-\d{4})", filename)
    if match_with_year:
        start, end = match_with_year.groups()
        return f"{start}-to-{end}"

    # Match without year
    match_without_year = re.search(r"SAVD-Decisions-(\d{1,2}-[A-Za-z]+)-to-(\d{1,2}-[A-Za-z]+)", filename)
    if match_without_year:
        start, end = match_without_year.groups()
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
                if "Application Number" in row[0] or "Decision" in row[1]:
                    continue
                if row[0] and row[1]:
                    rows.append([row[0].strip(), row[1].strip()])
    text_to_go = f"Extracted {len(rows)} rows from {os.path.basename(filepath)}"
    print(text_to_go)
    write_message(text_to_go) # write the stats to display on app!
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
    text_to_go = (f"Inserted {new_rows} new records.")
    print(text_to_go)
    write_message(' - '+text_to_go+'\n')

# === MAIN LOGIC ===
def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(TO_PROCESS_DIR, exist_ok=True)

    files = [f for f in os.listdir(TO_PROCESS_DIR) if f.lower().endswith(".pdf")]
    if not files:
        print("No PDFs to process.")
        return

    conn = init_db(DB_PATH)

    for filename in files:
        filepath = os.path.join(TO_PROCESS_DIR, filename)

        print(f"\nProcessing {filename}")
        week_label = extract_week_label(filename)
        rows = process_pdf(filepath, week_label)
        insert_into_db(conn, rows, week_label, filename)

        # Move processed file to "processed"
        dest_path = os.path.join(PROCESSED_DIR, filename)
        shutil.move(filepath, dest_path)
        print(f"Moved to processed: {filename}")

    print("\nDone. All PDFs processed.")


if __name__ == "__main__":
    main()
    
# === END OF FILE ===
# This script processes PDF files, extracts data, and stores it in a SQLite database.   
# It also manages file organization by moving processed files to a separate directory.
# It writes messages to a text file for display in the web app.
# === END OF FILE ===

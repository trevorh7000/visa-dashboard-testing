#!/home/trev/python/new_dev/bin/python3
# -*- coding: utf-8 -*-
"""
Main entry point for the data pipeline to scrape, process, and update the visa decisions database.
This script orchestrates the scraping of PDF links, processing of those PDFs,
and updating the Streamlit dashboard with new data.
"""

# /home/trev/Dropbox/programming/python/visa_dashboard_app/data_pipline/main.py


from scraper import run_scraper
from processor import run_processor
import logging
import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Change working directory to the script's directory
# removed as it was fucking me in the wrong directopry
#os.chdir(os.path.dirname(os.path.abspath(__file__)))

# added this
# Absolute path to where the DB actually lives
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'visa-dashboard-web')
DB_PATH = os.path.join(BASE_DIR, 'decisions.db')
#seems to be the corect path to the DB
# print (DB_PATH)
# sys.exit()



def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("/home/trev/VISAlogfile.log", mode="a")]
)
def check_last_run(conn):
    """
    Return last_updated and last_run as datetime objects,
    or None if a setting hasn’t been stored yet.
    """
    last_run_str = get_setting(conn, "last_run")
    last_updated_str = get_setting(conn, "last_updated")
    if last_run_str is None and last_updated_str is None:
        print ("No last run or last updated found.")
        return None, None
    last_run = datetime.fromisoformat(last_run_str) if last_run_str else None
    last_updated = datetime.fromisoformat(last_updated_str) if last_updated_str else None

    return last_updated, last_run


def get_setting(conn, setting):
    """Return the value for a setting, or None if it doesn’t exist."""
    row = conn.execute(
        "SELECT value FROM settings WHERE setting = ?",
        (setting,)
    ).fetchone()

    if row:
        return row[0]  # just the value
    return None



def main():
    print("📥 Starting scheduled data pipeline...")
    logging.info("STARTING scheduled data pipeline...") 
    conn = sqlite3.connect(DB_PATH)
    last_updated, last_run = check_last_run(conn)
    print(f"Last updated: {last_updated}, Last run: {last_run}")
    logging.info(f"Last updated: {last_updated}, Last run: {last_run}") 
    now = datetime.now()
    # if last_run and (now - last_run) < timedelta(hours=1):
    #     print("⏳ Last run was less than an hour ago. Exiting to prevent frequent executions.")
    #     logging.info("Last run was less than an hour ago. Exiting to prevent frequent executions.")
    #     return False
    sys.exit() # bug out for testing

    if run_scraper():
        print("🧮 Scraper ran successfully. Proceeding to processing...")
        new_records = run_processor()
        if new_records > 0:
            print(f"✅ {new_records} new records processed and pushed.")
            logging.info(f"New records processed and pushed: {new_records}")
        else:
            print("🟡 No new records found. No update pushed.")
            logging.info("No new records found. No update pushed.")
    else:
        print("❌ Scraper failed. Aborting pipeline.")
        logging.error("Scraper failed. Aborting pipeline.") 

if __name__ == "__main__":
    setup_logging(debug=True)
    main()

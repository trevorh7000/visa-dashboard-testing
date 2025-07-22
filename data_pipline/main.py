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

# Change working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("/home/trev/VISAlogfile.log", mode="a")]
)


def main():
    print("📥 Starting scheduled data pipeline...")
    logging.info("STARTING scheduled data pipeline...") 

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

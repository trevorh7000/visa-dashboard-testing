#!/usr/bin/env python3
# -*- coding: utf-8 -*- 
"""
Scraper for South Africa Visa Desk PDF links and downloads.
This script fetches PDF links from the South Africa Visa Desk page,
downloads them, and saves them to a specified directory.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

import logging
logger = logging.getLogger(__name__)


# === wrapping: moved config and path logic into a setup function
def setup():
    BASE_URL = "https://www.irishimmigration.ie/south-africa-visa-desk/#tourist"
    BASE_DIR = os.path.dirname(__file__)
    TO_PROCESS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "pdf", "to_process"))
    return BASE_URL, TO_PROCESS_DIR
# === end wrapping

def fetch_pdf_links(base_url):
    """Fetch all SAVD PDF links from the visa desk page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    response = requests.get(base_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", href=True)

    pdf_links = [
        urljoin(base_url, a['href'])
        for a in links
        if a['href'].lower().endswith(".pdf") and os.path.basename(a['href']).startswith("SAVD-")
    ]
    return pdf_links

def download_pdf(url, folder):
    filename = os.path.basename(url)
    filepath = os.path.join(folder, filename)

    if os.path.exists(filepath):
        print(f"Already downloaded: {filename}")
        return

    print(f"Downloading: {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

# === wrapping: main logic moved into run_scraper()
def run_scraper():
    try:
        BASE_URL, TO_PROCESS_DIR = setup()
        os.makedirs(TO_PROCESS_DIR, exist_ok=True)

        print("Fetching PDF links...")
        pdf_links = fetch_pdf_links(BASE_URL)
        print(f"Found {len(pdf_links)} total PDF(s).")
        logger.info(f"Found {len(pdf_links)} total PDF(s).")

        for link in pdf_links:
            try:
                download_pdf(link, TO_PROCESS_DIR)
            except Exception as e:
                print(f"Error downloading {link}: {e}")
                logger.error(f"Error downloading {link}: {e}")

        return True
    except Exception as e:
        print(f"❌ Scraper failed: {e}")
        logger.error(f"Scraper failed: {e}")
        return False
# === end wrapping

# === wrapping: safe entry point
if __name__ == "__main__":
    run_scraper()
# === end wrapping


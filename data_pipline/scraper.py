import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Configuration
BASE_URL = "https://www.irishimmigration.ie/south-africa-visa-desk/#tourist"

# Paths setup
BASE_DIR = os.path.dirname(__file__)
LOG_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "pdf", "downloaded_pdfs.txt"))
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "pdf"))
NEW_PDFS_FILE = os.path.join(OUTPUT_DIR, "new_pdfs.txt")


def fetch_pdf_links():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    response = requests.get(BASE_URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", href=True)
    pdf_links = [
        urljoin(BASE_URL, a['href'])
        for a in links
        if a['href'].lower().endswith(".pdf") and os.path.basename(a['href']).startswith("SAVD-")
    ]
    return pdf_links


def load_log_file(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return set(line.strip() for line in f)
    return set()


def save_downloaded_log(downloaded):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        for item in sorted(downloaded):
            f.write(item + "\n")


def append_to_new_pdfs(link):
    """Ensure the link is added to new_pdfs.txt, unless it's already there."""
    os.makedirs(os.path.dirname(NEW_PDFS_FILE), exist_ok=True)
    existing = load_log_file(NEW_PDFS_FILE)
    if link not in existing:
        with open(NEW_PDFS_FILE, "a") as f:
            f.write(link + "\n")


def download_pdf(url, folder):
    local_filename = os.path.join(folder, os.path.basename(url))
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(local_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return local_filename


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Fetching PDF links...")
    pdf_links = fetch_pdf_links()

    downloaded = load_log_file(LOG_FILE)

    new_to_download = [link for link in pdf_links if link not in downloaded]

    print(f"Found {len(new_to_download)} PDFs not yet downloaded.")

    for link in new_to_download:
        try:
            print(f"Downloading: {link}")
            download_pdf(link, OUTPUT_DIR)
            downloaded.add(link)

            # ✅ Append to new_pdfs.txt *after* download
            append_to_new_pdfs(link)

        except Exception as e:
            print(f"Error downloading {link}: {e}")

    if new_to_download:
        save_downloaded_log(downloaded)
    else:
        print("No new PDFs to download.")

if __name__ == "__main__":
    main()

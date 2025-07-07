import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Configuration
BASE_URL = "https://www.irishimmigration.ie/south-africa-visa-desk/#tourist"

# Get current script directory (whether you're in data_pipline or streamlit app)
BASE_DIR = os.path.dirname(__file__)

# Path to ../data/downloaded_pdfs.txt
LOG_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "pdf", "downloaded_pdfs.txt"))
print("LOG_FILE path (resolved):", os.path.abspath(LOG_FILE))
# Path to where doanloaded PDFs will be saved
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "pdf"))


def fetch_pdf_links():
    """Fetch all PDF links from the target site using browser-like headers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
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


def load_downloaded_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_downloaded_log(downloaded):
    # Ensure the parent directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    with open(LOG_FILE, "w") as f:
        for item in sorted(downloaded):
            f.write(item + "\n")

def download_pdf(url, folder):
    local_filename = os.path.join(folder, url.split("/")[-1])
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

    downloaded = load_downloaded_log()
    new_links = [link for link in pdf_links if link not in downloaded]

    print(f"Found {len(new_links)} new PDFs.")
    for link in new_links:
        try:
            print(f"Downloading: {link}")
            download_pdf(link, OUTPUT_DIR)
            downloaded.add(link)
        except Exception as e:
            print(f"Error downloading {link}: {e}")

    save_downloaded_log(downloaded)

    # Optional: write new PDFs to a separate file for stage two
    with open(os.path.join(OUTPUT_DIR, "new_pdfs.txt"), "w") as f:
        for link in new_links:
            f.write(link + "\n")

if __name__ == "__main__":
    main()

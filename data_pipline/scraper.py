import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# --- Configuration ---
BASE_URL = "https://www.irishimmigration.ie/south-africa-visa-desk/#tourist"

# --- Path setup ---
BASE_DIR = os.path.dirname(__file__)
TO_PROCESS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "pdf", "to_process"))

def fetch_pdf_links():
    """Fetch all SAVD PDF links from the visa desk page."""
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

def main():
    os.makedirs(TO_PROCESS_DIR, exist_ok=True)

    print("Fetching PDF links...")
    pdf_links = fetch_pdf_links()
    print(f"Found {len(pdf_links)} total PDF(s).")

    for link in pdf_links:
        try:
            download_pdf(link, TO_PROCESS_DIR)
        except Exception as e:
            print(f"Error downloading {link}: {e}")

if __name__ == "__main__":
    main()

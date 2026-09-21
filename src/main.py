import requests
import os

CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"
CACHE_PATH = "cache/catalogue-page-1.html"

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/dishaagowda/scraper)"


def fetch_page(url, cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT — {len(html)} bytes")
        return html

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print(f"FETCH FAILED — status {response.status_code}")
        return None

    html = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"FETCH — {len(html)} bytes, status {response.status_code}")
    return html


if __name__ == "__main__":
    fetch_page(CATALOGUE_URL, CACHE_PATH)
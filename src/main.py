import requests
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
CACHE_DIR = "cache"

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/dishaagowda/scraper)"


def fetch_page(url, cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT — {len(html)} bytes — {url}")
        return html

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print(f"FETCH FAILED — status {response.status_code} — {url}")
        return None

    html = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"FETCH — {len(html)} bytes, status {response.status_code} — {url}")
    time.sleep(0.5)
    return html


def discover_catalogue_pages():
    all_book_links = []
    page_num = 1
    MAX_PAGES = 3

    while page_num <= MAX_PAGES:
        url = BASE_URL.format(page_num)
        cache_path = f"{CACHE_DIR}/catalogue-page-{page_num}.html"
        html = fetch_page(url, cache_path)

        if html is None:
            break

        soup = BeautifulSoup(html, "html.parser")
        book_links = soup.select("article.product_pod h3 a")

        for link in book_links:
            href = link.get("href")
            absolute_url = urljoin(url, href)
            all_book_links.append(absolute_url)

        page_num += 1

    unique_urls = list(set(all_book_links))
    print(f"catalogue_pages={min(page_num - 1, MAX_PAGES)} discovered={len(all_book_links)} unique_urls={len(unique_urls)}")
    return unique_urls


if __name__ == "__main__":
    urls = discover_catalogue_pages()
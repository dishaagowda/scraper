import requests
import os
import re
import time
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
from pydantic import BaseModel, ValidationError, HttpUrl

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
CACHE_DIR = "cache"
OUTPUT_DIR = "output"

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/dishaagowda/scraper)"

# One deliberately broken URL to prove the run survives a bad page
FAKE_BROKEN_URL = "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html"


class Book(BaseModel):
    title: str
    product_url: HttpUrl
    price_gbp: float
    price_text: str
    availability_text: str
    rating_text: str
    description: str | None
    source_page: str
    fetched_at: str


def fetch_page(url, cache_path, retries_left=1):
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT — {len(html)} bytes — {url}")
        return html, True

    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        if retries_left > 0:
            time.sleep(1)
            return fetch_page(url, cache_path, retries_left - 1)
        print(f"FETCH FAILED — request error — {url}")
        return None, False

    response.encoding = "utf-8"

    if response.status_code == 404 or response.status_code == 403:
        print(f"FETCH FAILED — status {response.status_code} (no retry) — {url}")
        return None, False

    if response.status_code >= 500 and retries_left > 0:
        time.sleep(1)
        return fetch_page(url, cache_path, retries_left - 1)

    if response.status_code != 200:
        print(f"FETCH FAILED — status {response.status_code} — {url}")
        return None, False

    html = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"FETCH — {len(html)} bytes, status {response.status_code} — {url}")
    time.sleep(0.5)
    return html, False


def discover_catalogue_pages():
    all_book_links = []
    page_num = 1
    MAX_PAGES = 3

    while page_num <= MAX_PAGES:
        url = BASE_URL.format(page_num)
        cache_path = f"{CACHE_DIR}/catalogue-page-{page_num}.html"
        html, _ = fetch_page(url, cache_path)

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

    # Inject one deliberately broken URL to prove the run survives it
    unique_urls.append(FAKE_BROKEN_URL)
    return unique_urls


def extract_book(book_url, source_page):
    safe_name = book_url.rstrip("/").split("/")[-2]
    cache_path = f"{CACHE_DIR}/book-{safe_name}.html"
    html, from_cache = fetch_page(book_url, cache_path)

    if html is None:
        return None, from_cache

    soup = BeautifulSoup(html, "html.parser")
    product_main = soup.select_one("div.product_main")

    title = product_main.select_one("h1").get_text(strip=True)
    price_text = product_main.select_one("p.price_color").get_text(strip=True)
    availability_text = product_main.select_one("p.availability").get_text(strip=True)

    rating_tag = product_main.select_one("p.star-rating")
    rating_text = rating_tag["class"][1] if rating_tag else None

    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.get_text(strip=True) if description_tag else None

    record = {
        "title": title,
        "product_url": book_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }
    return record, from_cache


def normalize_record(raw):
    price_match = re.search(r"[\d.]+", raw["price_text"])
    price_gbp = float(price_match.group()) if price_match else None
    return {**raw, "price_gbp": price_gbp}


def validate_record(record):
    try:
        book = Book(**record)
        return book.model_dump(mode="json"), None
    except ValidationError as e:
        return None, str(e)


if __name__ == "__main__":
    start_time = datetime.now(timezone.utc)

    urls = discover_catalogue_pages()

    valid_records = []
    error_records = []
    seen_urls = set()
    cache_hits = 0
    failed_pages = 0
    pages_fetched = 0

    for url in urls:
        try:
            raw, from_cache = extract_book(url, source_page=url)
        except Exception as e:
            error_records.append({"url": url, "reason": f"unexpected error: {e}"})
            failed_pages += 1
            continue

        if raw is None:
            error_records.append({"url": url, "reason": "fetch failed"})
            failed_pages += 1
            continue

        if from_cache:
            cache_hits += 1
        else:
            pages_fetched += 1

        normalized = normalize_record(raw)

        if normalized["product_url"] in seen_urls:
            continue
        seen_urls.add(normalized["product_url"])

        validated, error = validate_record(normalized)
        if validated:
            valid_records.append(validated)
        else:
            error_records.append({"url": url, "reason": error})

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(f"{OUTPUT_DIR}/books.json", "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)

    with open(f"{OUTPUT_DIR}/errors.json", "w", encoding="utf-8") as f:
        json.dump(error_records, f, indent=2, ensure_ascii=False)

    end_time = datetime.now(timezone.utc)

    report = {
        "start_time": start_time.isoformat(),
        "duration_seconds": (end_time - start_time).total_seconds(),
        "pages_fetched": pages_fetched,
        "cache_hits": cache_hits,
        "valid_records": len(valid_records),
        "invalid_records": len(error_records) - failed_pages,
        "failed_pages": failed_pages
    }

    with open(f"{OUTPUT_DIR}/run-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"valid_records={len(valid_records)} error_records={len(error_records)} failed_pages={failed_pages}")
    print(report)

    
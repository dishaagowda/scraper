# The Polite Scraper

A small scraping pipeline that downloads book data from a public practice sandbox, 
turns messy HTML into clean, validated JSON, and survives broken pages without crashing.

## Target Classification

- **Site:** [Books to Scrape](https://books.toscrape.com) — a public sandbox built 
  specifically for scraping practice (confirmed on toscrape.com).
- **Scope:** the first 3 catalogue pages only (60 unique books total).
- **robots.txt check:** requested `https://books.toscrape.com/robots.txt` — result: 
  404 Not Found (no robots file found). A missing file is not permission, just an 
  absence of a written rule.
- **Data collected:** book title, price, availability, rating, description, and 
  product URL — all publicly visible on the page.
- **Why this is appropriate:** the site exists explicitly for scraping practice, and 
  this scraper only collects a small, bounded set of publicly visible data at a 
  polite pace.

I will not reuse this code on another site without checking its rules and terms first.

## How to Run

**Requirements:** Python 3.10+

```bash
git clone https://github.com/dishaagowda/scraper.git
cd scraper
pip3 install requests beautifulsoup4 pydantic
python3 src/main.py
```

This produces `output/books.json`, `output/errors.json`, and `output/run-report.json`.

## Record Schema

Each validated record in `books.json` has:

| Field | Type | Description |
|---|---|---|
| title | string | Book title |
| product_url | URL | Canonical product page URL |
| price_gbp | number | Price as a real number, e.g. 51.77 |
| price_text | string | Original price text, e.g. "£51.77" |
| availability_text | string | Original availability text from the page |
| rating_text | string | Star rating as text (One–Five) |
| description | string or null | Book description, null if not present on the page |
| source_page | string | The catalogue page this book was discovered on |
| fetched_at | string | ISO timestamp of when the page was fetched |

## Politeness Rules

- **User-agent:** every request identifies itself as `FlyRankInternshipA9/1.0` with a link back to this repo.
- **Delay:** at least 500ms between real requests to the site — cached pages need no delay.
- **Timeout:** every request gives up after 10 seconds rather than hanging forever.
- **Status check:** only a `200` response is treated as a real page; anything else is a failed fetch, not HTML to parse.
- **Cache:** every page is saved locally after the first fetch, so re-running during development never re-hits the site.
- **Retry rules:** a `5xx` server error or network timeout gets one retry after a short wait. A `404` or `403` is never retried — the page doesn't exist, or the site said no.

## Sample Run Report

```json
{
  "start_time": "2026-09-21T15:46:30.121295+00:00",
  "duration_seconds": 0.995832,
  "pages_fetched": 0,
  "cache_hits": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
```

## Why No Browser Was Needed

The book data (title, price, availability, rating, description) is already present in the 
HTML the server sends back — there is no JavaScript rendering step that hides it. Using a 
full browser (like Playwright) here would only add cost — slower requests, more memory, more 
complexity — for the same data a plain HTTP request already returns.

## Ethics Note

This scraper only touches Books to Scrape, a site built specifically for scraping practice. 
In general: use an official API when one exists rather than scraping; never bypass logins, 
paywalls, or explicit blocks; and only collect the data actually needed for the task. I will 
not reuse this code on another site without checking its rules and terms of service first.

## Known Limitation

Some description fields contain duplicated text due to how the source page structures its 
content — this doesn't affect data validity (the description is still accurate), just its 
formatting.

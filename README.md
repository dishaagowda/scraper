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

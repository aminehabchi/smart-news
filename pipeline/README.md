# pipeline

The data-processing pipeline of the NLP Scraper project.

`orchestrator.py` scrapes the latest articles from techcrunch.com/latest/
with Playwright and stores them in MongoDB (`storage`). NLP processing
(keywords, sentiment, NER) is not implemented yet.

## Structure

- `scrapers/techcrunch.py` — Playwright scraper. `scrape_latest(limit=20)` returns a list of dicts:
  `creation_date` (when scraped), `publish_date`, `title`, `body`, `topics` (array),
  `author` (`{name, link}`), `url`.
- `db.py` — MongoDB access (`MONGO_URI` from the root `.env`), upserts articles by `url`.
- `orchestrator.py` — entry point: scrape then insert.

## Setup

```bash
./setup.sh
```

## Run

```bash
./run.sh
```

Requires `storage` (MongoDB) to be running.

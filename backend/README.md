# backend

The API layer of the NLP Scraper project, built with FastAPI.

Serves the articles stored in MongoDB (`storage`) by `pipeline`, for
`frontend` to consume, and runs the scraping pipeline itself on an hourly
schedule (see `scheduler.py`).

## Endpoints

Articles:

- `GET /api/articles` — paginated, filterable article list, sorted by `creation_date`.
  Query params: `page`, `page_size`, `q` (full-text search), `source`, `predicted_topic`, `title`, `body`, `persons`, `organizations`, `locations`, `dates_times`, `quantities_percentages` (substring match), `sentiment` (`positive`/`neutral`/`negative`), `order` (`newest`/`oldest`).
  Returns `{ items, page, page_size, total, total_pages }`.
- `GET /api/articles/export` — same filters as above (no pagination), streamed as a CSV file (`Content-Disposition: attachment`). Columns mirror everything shown on an article's detail page: id, title, source, author name/link, publish/creation date, predicted topic, topics, full sentiment scores, all entity groups, saved status, url, and body.
- `GET /api/articles/{id}` — single article by id.
- `GET /api/articles/{id}/related?limit=5` — other articles scored by shared topic/entities/sentiment closeness.
- `GET /api/articles/{id}/cross-source` — the article plus the best matching article from each *other* source for the same story (stricter entity/topic-overlap threshold than `/related`), for comparing how sources cover the same story.
- `PUT /api/articles/{id}/save?saved=true` — toggle save-for-later.
- `GET /api/saved` — all saved articles.

Reference lists:

- `GET /api/sources` — distinct article sources.
- `GET /api/topics` — distinct `predicted_topic` values.

Aggregates:

- `GET /api/stats` — total article count, counts by topic/source/sentiment, top entities (persons/organizations/locations), and a 30-day daily sentiment trend.

Pipeline:

- `GET /api/pipeline/runs?limit=20` — recent scrape-pipeline runs (scheduled or manual), with status/duration/output.
- `POST /api/pipeline/run` — trigger a pipeline run in the background; `409` if one is already in progress.

## Setup

```bash
./setup.sh
```

## Run

```bash
./run.sh
```

Requires `storage` (MongoDB) to be running. Serves on `http://localhost:8000`
(configurable via `APP_HOST`/`APP_PORT` in the root `.env`). Interactive docs
at `/docs`.

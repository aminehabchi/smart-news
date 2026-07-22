# app

The API layer of the NLP Scraper project, built with FastAPI.

Serves the articles stored in MongoDB (`storage`) by `pipeline`, with
pagination, for `frontend` to consume.

## Endpoints

- `GET /api/articles?page=1&page_size=20` — paginated article list, sorted by `publish_date` descending.
  Returns `{ items, page, page_size, total, total_pages }`.
- `GET /api/articles/{id}` — single article by id.

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

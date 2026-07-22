# frontend

The UI of the NLP Scraper project, built with Angular (generated via
`ng new`, standalone components, routing).

Displays the articles stored in `storage` (MongoDB), served by `backend`'s API.

## Structure

- `src/app/models/article.model.ts` — `Article`/`ArticlePage` types matching the API response.
- `src/app/services/article.ts` — `ArticleService`, calls `GET /api/articles` (paginated list) and `GET /api/articles/:id`.
- `src/app/components/article-list` — home route (`/`), paginated article list.
- `src/app/components/article-detail` — route `/articles/:id`, full article view.
- `src/app/config.ts` — `API_BASE_URL`, currently hardcoded to `http://localhost:8000/api`.

## Setup

```bash
./setup.sh
```

## Run

```bash
./run.sh
```

Requires `backend` (the API) running on `http://localhost:8000` and `storage` (MongoDB) up.

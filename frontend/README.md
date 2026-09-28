# frontend

The UI of the NLP Scraper project, built with Angular (generated via
`ng new`, standalone components, routing, signals).

Displays the articles stored in `storage` (MongoDB), served by `backend`'s API.

## Structure

Models (types matching the API response):

- `models/article.model.ts` — `Article`, `ArticlePage`.
- `models/stats.model.ts` — `Stats`, `CountItem`, `EntityCount`, `DailySentimentCount`.
- `models/pipeline.model.ts` — `PipelineRun`.

Services:

- `services/article.ts` — `ArticleService`: paginated/filtered list (`GET /api/articles`), CSV export URL builder, single article, related articles, sources/topics reference lists, save-for-later toggle.
- `services/saved-articles.ts` — `SavedArticlesService`: save-for-later state.
- `services/stats.ts` — `StatsService`: `GET /api/stats`.
- `services/pipeline.ts` — `PipelineService`: pipeline run history and manual trigger.

Components/routes:

- `components/article-list` — home route (`/`), paginated article list: source chips, full-text search, sentiment/entity/predicted-topic advanced filters (kept in the URL), sort order, CSV export of the current filter, clickable predicted-topic badges.
- `components/article-detail` — route `/articles/:id`, full article view: extracted entities and predicted topic (both clickable, filtering back into the article list), sentiment breakdown, related articles, save-for-later.
- `components/stats-page` — route `/stats`, aggregate dashboard: totals, articles by topic/source, a 30-day sentiment trend chart, sentiment breakdown, top entities.
- `components/pipeline-page` — route `/pipeline`, scrape-pipeline run history and a manual "Run now" trigger.
- `components/saved-list` — route `/saved`, saved-for-later articles.
- `components/about` — route `/about`.
- `components/header`, `components/bar-list` — shared nav bar and a reusable labeled-bar-chart component (used by the stats dashboard).

Pipes:

- `pipes/source-name-pipe.ts` — formats a raw source hostname for display.
- `pipes/reading-time-pipe.ts` — estimates reading time from article body length.

Config:

- `config.ts` — `API_BASE_URL`, currently hardcoded to `http://localhost:8001/api`.

## Setup

```bash
./setup.sh
```

## Run

```bash
./run.sh
```

Requires `backend` (the API) running on `http://localhost:8001` and `storage` (MongoDB) up.

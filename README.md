# NLP Scraper

A full-stack pipeline that scrapes tech news (TechCrunch, The Verge, Ars
Technica), cleans and analyzes it with NLP — named entity recognition
(persons, organizations, locations, dates/times, quantities) and automatic
topic classification (business/entertainment/politics/sport/tech) — stores
the results in MongoDB, and serves them through a REST API and an Angular UI
with full-text search, entity/topic filtering, and save-for-later.

## Architecture

- `storage/` — MongoDB, run via Docker Compose.
- `pipeline/` — Playwright scrapers + text cleaning (tokenize, stopword removal, stemming) + NER (spaCy) + topic classification (TF-IDF + LogisticRegression, `pipeline/topic_classifier/`, trained on the BBC News dataset). Own venv, shared by all of the above.
- `backend/` — FastAPI REST API over the stored articles (search, filters, save-for-later). Also runs the scraping pipeline on an hourly schedule. Own venv.
- `frontend/` — Angular UI: browse/search/filter articles, view extracted entities and predicted topic, save articles for later.

Each directory has its own `README.md` with structure/endpoint details.

## Prerequisites

- Docker (for MongoDB)
- Python 3.11+ with `venv`
- Node.js + npm (for the Angular frontend)

## Setup & run

Run these in order — later components depend on earlier ones being up and,
for the pipeline/classifier, having already populated data.

Steps 3–6 each install their component's dependencies via its own
`setup.sh`. To install all of them in one go, run `./setup.sh` from the repo
root (it just calls `pipeline/setup.sh`, `pipeline/topic_classifier/setup.sh`,
`backend/setup.sh`, and `frontend/setup.sh` in order) — then skip straight to
each component's `run.sh`/`classify.sh` below.

### 1. Configure environment

```bash
cp .env.example .env
# edit .env if you want different Mongo credentials/ports or app host/port
```

### 2. Start MongoDB

```bash
cd storage && docker compose --env-file ../.env up -d && cd ..
```

### 3. Train the topic classifier

Optional, but do this before step 4 so newly scraped articles get a
`predicted_topic` immediately instead of needing a backfill run later.

```bash
./pipeline/setup.sh
./pipeline/topic_classifier/setup.sh
./pipeline/topic_classifier/run.sh   # trains the model on the bundled BBC News dataset
```

### 4. Scrape + clean + extract entities + classify topics

```bash
./pipeline/run.sh   # scrapes latest articles, cleans text, runs NER and topic
                     # classification on them, stores the result in MongoDB
```

If you skipped step 3, or want to (re-)process articles stored before the
classifier was trained, these self-tracking backfill scripts only touch
articles missing the relevant field:

```bash
./pipeline/nlp_engine/run.sh             # backfill NER
./pipeline/topic_classifier/classify.sh  # backfill topic classification
```

### 5. Start the backend API

Serves `http://localhost:8000`, and re-runs the scraping pipeline every hour
automatically.

```bash
./backend/setup.sh
./backend/run.sh   # starts in the background, logs to backend/backend.log
```

### 6. Start the frontend

Serves `http://localhost:4200`.

```bash
./frontend/setup.sh
./frontend/run.sh  # starts in the background, logs to frontend/frontend.log
```

Then open `http://localhost:4200`. Interactive API docs are at
`http://localhost:8000/docs`.

## Stopping

`backend` and `frontend` run as background processes (PIDs tracked in
`./pids`):

```bash
./backend/stop.sh
./frontend/stop.sh
```

`storage` is a Docker Compose service:

```bash
cd storage && docker compose down
```

# NLP Scraper

A full-stack pipeline that scrapes tech news (TechCrunch, The Verge, Ars
Technica), cleans and analyzes it with NLP — named entity recognition
(persons, organizations, locations, dates/times, quantities) and automatic
topic classification (business/entertainment/politics/sport/tech) — stores
the results in MongoDB, and serves them through a REST API and an Angular UI
with full-text search, entity/topic filtering, and save-for-later.

## Architecture

- `storage/` — MongoDB, run via Docker Compose.
- `pipeline/` — Playwright scrapers + text cleaning (tokenize, stopword removal, stemming) + NER (spaCy). Own venv.
- `topic_classifier/` — standalone TF-IDF + LogisticRegression classifier (trained on the BBC News dataset) that predicts each article's topic. Own venv.
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

### 1. Configure environment

```bash
cp .env.example .env
# edit .env if you want different Mongo credentials/ports or app host/port
```

### 2. Start MongoDB

```bash
cd storage && docker compose --env-file ../.env up -d && cd ..
```

### 3. Scrape + clean + extract entities

```bash
./pipeline/setup.sh
./pipeline/run.sh              # scrapes latest articles, cleans text, stores in MongoDB
./pipeline/nlp_engine/run.sh   # runs NER over stored articles
```

### 4. Classify article topics

Optional, but pairs with the NER step above.

```bash
./topic_classifier/setup.sh
./topic_classifier/run.sh      # trains the model on the bundled BBC News dataset
./topic_classifier/classify.sh # predicts a topic for every stored article
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

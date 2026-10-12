# SmartNews

A full-stack pipeline that scrapes tech news (TechCrunch, The Verge, Ars
Technica), cleans and analyzes it with NLP — named entity recognition
(persons, organizations, locations, dates/times, quantities), automatic
topic classification (business/entertainment/politics/sport/tech), and
sentiment analysis (VADER) — stores the results in MongoDB, and serves them
through a REST API and an Angular UI with full-text search, entity/topic/
sentiment filtering, CSV export of any filtered view, related-article
suggestions, a stats dashboard (including a 30-day sentiment trend), a
pipeline run-history/manual-trigger view, and save-for-later.

![SmartNews UI](docs/screenshot.png)

## Tech stack

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Angular](https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white)](https://angular.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/)
[![spaCy](https://img.shields.io/badge/spaCy-09A3D5?style=for-the-badge&logo=spacy&logoColor=white)](https://spacy.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)

## Architecture

- `storage/` — MongoDB, run via Docker Compose.
- `pipeline/` — Playwright scrapers + text cleaning (tokenize, stopword removal, stemming) + NER (spaCy) + sentiment analysis (NLTK VADER) + topic classification (TF-IDF + LogisticRegression, `pipeline/topic_classifier/`, trained on the BBC News dataset). Own venv, shared by all of the above.
- `backend/` — FastAPI REST API over the stored articles (search, filters, CSV export, related-article/cross-source suggestions, aggregate stats, save-for-later). Also runs the scraping pipeline on an hourly schedule, and tracks/exposes pipeline run history plus a manual-trigger endpoint. Own venv.
- `frontend/` — Angular UI: browse/search/filter articles (including by sentiment and predicted topic, with CSV export of the current filter), view extracted entities/predicted topic/sentiment breakdown, jump to related articles, a stats dashboard (including a 30-day sentiment trend), a pipeline run-history/manual-trigger page, and save articles for later.

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

### 4. Scrape + clean + extract entities + score sentiment + classify topics

```bash
./pipeline/run.sh   # scrapes latest articles, cleans text, runs NER, sentiment
                     # analysis, and topic classification on them, stores the
                     # result in MongoDB
```

If you skipped step 3, or want to (re-)process articles stored before the
classifier was trained, these self-tracking backfill scripts only touch
articles missing the relevant field:

```bash
./pipeline/nlp_engine/run.sh             # backfill NER + sentiment
./pipeline/topic_classifier/classify.sh  # backfill topic classification
```

### 5. Start the backend API

Serves `http://localhost:8001`, and re-runs the scraping pipeline every hour
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
`http://localhost:8001/docs`.

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

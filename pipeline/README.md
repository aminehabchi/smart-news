# pipeline

The data-processing pipeline of the NLP Scraper project.

`orchestrator.py` scrapes the latest articles from TechCrunch, The Verge,
and Ars Technica with Playwright, cleans the text, runs NER, scores
sentiment, predicts a topic category, and stores the result in MongoDB
(`storage`) in a single pass.

## Structure

- `scrapers/{techcrunch,theverge,arstechnica}.py` — Playwright scrapers. Each `scrape_latest(limit=20)` returns a list of dicts:
  `creation_date` (when scraped), `publish_date`, `title`, `body`, `topics` (array),
  `author` (`{name, link}`), `url`, `source`.
- `text_preprocessing/preprocessing.py` — cleans scraped text and produces derived fields (`clean_text`, `stemmed_tokens`) via tokenization, stopword removal, and stemming, without touching the original `body` (NER needs original casing).
- `text_preprocessing/bow.py` — bag-of-words vectorization helpers (corpus fitting, token-to-id mapping, word frequencies) used for the word-frequency stats stored alongside articles.
- `nlp_engine/ner.py` — Named Entity Recognition (spaCy) over the raw title/body/topics: persons, organizations, locations, dates/times, quantities & percentages.
- `nlp_engine/sentiment.py` — sentiment scoring (NLTK VADER) over the raw article body: `neg`/`neu`/`pos`/`compound`.
- `nlp_engine/orchestrator.py`, `nlp_engine/sentiment_orchestrator.py` — self-tracking backfill scripts that (re-)run NER/sentiment only on articles missing the respective field. Independent of `pipeline/orchestrator.py`, which already runs both stages inline for freshly scraped articles.
- `topic_classifier/` — topic classification (business/entertainment/politics/sport/tech): TF-IDF + LogisticRegression, trained on the bundled BBC News dataset.
  - `training/prepare_data.py`, `training/train.py`, `training/evaluate.py` — data prep, training, and evaluation scripts; produce `model/topic_classifier.pkl`.
  - `orchestrator.py` — self-tracking backfill script that predicts `predicted_topic` for any article the model hasn't classified yet, reusing the article's already-computed `stemmed_tokens` so cleaning is identical between training and inference.
- `db.py` — MongoDB access (`MONGO_URI` from the root `.env`); upserts articles by `url`, plus word-frequency storage.
- `model.py` — `Article`/`Entities`/`Sentiment` dataclasses shared across the pipeline.
- `orchestrator.py` — main entry point: scrape (all three sources) → clean → NER → sentiment → topic prediction → store, in one pass.

## Setup

```bash
./setup.sh
./topic_classifier/setup.sh
```

## Run

```bash
./run.sh                    # scrape + clean + NER + sentiment + topic classification
./topic_classifier/run.sh   # trains/retrains the topic classifier on the bundled dataset
./nlp_engine/run.sh          # backfill: NER + sentiment for articles missing either
./topic_classifier/classify.sh  # backfill: predicted_topic for unclassified articles
```

Requires `storage` (MongoDB) to be running. `backend` also re-runs
`./run.sh` automatically on an hourly schedule, and can trigger it on demand
via `POST /api/pipeline/run` (see `backend/README.md`).

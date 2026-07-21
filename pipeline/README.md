# pipeline

The data-processing pipeline of the NLP Scraper project.

Orchestrates the end-to-end flow: scrape web pages, clean the HTML into raw
text, then run NLP tasks (keyword extraction, sentiment analysis, named
entity recognition) before handing the results off to `storage`.

## Status

`orchestrator.py` is a placeholder (empty). Scaffolding only
(`requirements.txt`, `setup.sh`, `run.sh`).

## Setup

```bash
./setup.sh
```

## Run

```bash
./run.sh
```

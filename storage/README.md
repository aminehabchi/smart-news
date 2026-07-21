# storage

The persistence layer of the NLP Scraper project.

Stores the scraped and NLP-analyzed data (text, keywords, sentiment,
entities) produced by `pipeline`, so it can be queried by `app`.

## Status

Not implemented yet. `Dockerfile` and `docker-compose.yml` are empty
skeletons to be filled in once the storage engine is chosen.

## Run (once implemented)

```bash
docker compose up
```

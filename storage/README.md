# storage

The persistence layer of the SmartNews project.

Stores the scraped and NLP-analyzed data (text, keywords, sentiment,
entities) produced by `pipeline`, so it can be queried by `backend`.

Storage engine: **MongoDB**.

## Status

`Dockerfile` builds the `mongo:7` image (extend it with init scripts under
`docker-entrypoint-initdb.d/` if needed). `docker-compose.yml` runs it with
credentials pulled from the root `.env`.

## Run

From this directory, pointing at the root `.env`:

```bash
docker compose --env-file ../.env up -d
```


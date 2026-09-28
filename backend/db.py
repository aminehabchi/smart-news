"""MongoDB access for the API."""

import logging
import os

from pymongo import MongoClient
from pymongo.collection import Collection

logger = logging.getLogger("db")

ARTICLES_COLLECTION = "articles"
PIPELINE_RUNS_COLLECTION = "pipeline_runs"
# URLs of articles deleted via the API -- the pipeline skips these so a
# deleted article isn't re-inserted on the next scrape.
DELETED_URLS_COLLECTION = "deleted_urls"

_client: MongoClient | None = None


def get_collection(name: str = ARTICLES_COLLECTION) -> Collection:
    global _client
    if _client is None:
        logger.info("Connecting to MongoDB")
        _client = MongoClient(os.environ["MONGO_URI"])
    db = _client.get_default_database()
    return db[name]


def ensure_indexes() -> None:
    logger.info("Ensuring MongoDB indexes")
    get_collection().create_index(
        [("title", "text"), ("body", "text"), ("topics", "text")],
        name="article_search",
    )
    get_collection().create_index("saved")
    get_collection(PIPELINE_RUNS_COLLECTION).create_index("status")
    get_collection(PIPELINE_RUNS_COLLECTION).create_index("started_at")
    get_collection(DELETED_URLS_COLLECTION).create_index("url", unique=True)

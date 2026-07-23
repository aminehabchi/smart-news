"""MongoDB access for the API."""

import logging
import os

from pymongo import MongoClient
from pymongo.collection import Collection

logger = logging.getLogger("db")

ARTICLES_COLLECTION = "articles"

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

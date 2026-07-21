"""MongoDB access for the API."""

import os

from pymongo import MongoClient
from pymongo.collection import Collection

ARTICLES_COLLECTION = "articles"

_client: MongoClient | None = None


def get_collection(name: str = ARTICLES_COLLECTION) -> Collection:
    global _client
    if _client is None:
        _client = MongoClient(os.environ["MONGO_URI"])
    db = _client.get_default_database()
    return db[name]


def ensure_indexes() -> None:
    get_collection().create_index(
        [("title", "text"), ("body", "text"), ("topics", "text")],
        name="article_search",
    )

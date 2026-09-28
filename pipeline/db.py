"""MongoDB access for the pipeline."""

import logging
import os

from pymongo import MongoClient
from pymongo.collection import Collection

from model import Article

logger = logging.getLogger("db")

ARTICLES_COLLECTION = "articles"
WORD_FREQUENCIES_COLLECTION = "word_frequencies"
# Written by the API when an article is deleted; see backend/db.py.
DELETED_URLS_COLLECTION = "deleted_urls"


def get_collection(name: str = ARTICLES_COLLECTION) -> Collection:
    uri = os.environ["MONGO_URI"]
    client = MongoClient(uri)
    db = client.get_default_database()
    return db[name]


def get_deleted_urls() -> set[str]:
    return {doc["url"] for doc in get_collection(DELETED_URLS_COLLECTION).find({}, {"url": 1})}


def insert_articles(articles: list[Article]) -> None:
    collection = get_collection()
    for article in articles:
        doc = article.model_dump(exclude={"id"})
        collection.update_one(
            {"url": doc["url"]},
            {"$set": doc},
            upsert=True,
        )
    logger.info("Upserted %d articles into MongoDB", len(articles))


def insert_word_frequencies(doc: dict) -> None:
    get_collection(WORD_FREQUENCIES_COLLECTION).insert_one(doc)
    logger.info("Stored word_frequencies for run_date=%s", doc.get("run_date"))

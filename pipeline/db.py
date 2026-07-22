"""MongoDB access for the pipeline."""

import os

from pymongo import MongoClient
from pymongo.collection import Collection

from model import Article

ARTICLES_COLLECTION = "articles"
WORD_FREQUENCIES_COLLECTION = "word_frequencies"


def get_collection(name: str = ARTICLES_COLLECTION) -> Collection:
    uri = os.environ["MONGO_URI"]
    client = MongoClient(uri)
    db = client.get_default_database()
    return db[name]


def insert_articles(articles: list[Article]) -> None:
    collection = get_collection()
    for article in articles:
        doc = article.model_dump(exclude={"id"})
        collection.update_one(
            {"url": doc["url"]},
            {"$set": doc},
            upsert=True,
        )


def insert_word_frequencies(doc: dict) -> None:
    get_collection(WORD_FREQUENCIES_COLLECTION).insert_one(doc)

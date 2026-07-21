"""MongoDB access for the pipeline."""

import os

from pymongo import MongoClient
from pymongo.collection import Collection

ARTICLES_COLLECTION = "articles"


def get_collection(name: str = ARTICLES_COLLECTION) -> Collection:
    uri = os.environ["MONGO_URI"]
    client = MongoClient(uri)
    db = client.get_default_database()
    return db[name]


def insert_articles(articles: list[dict]) -> None:
    collection = get_collection()
    for article in articles:
        collection.update_one(
            {"url": article["url"]},
            {"$set": article},
            upsert=True,
        )

import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import ReturnDocument

from db import ensure_indexes, get_collection
from models import Article, ArticlePage, CountItem, EntityCount, Stats
from scheduler import start_scheduler

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up")
    ensure_indexes()
    scheduler = start_scheduler()
    logger.info("Startup complete, hourly pipeline scheduler running")
    yield
    logger.info("Shutting down")
    scheduler.shutdown()


app = FastAPI(title="NLP Scraper API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["GET", "PUT"],
    allow_headers=["*"],
)


def _to_article(doc: dict) -> Article:
    doc["id"] = str(doc.pop("_id"))
    return Article(**doc)


def _contains(value: str) -> dict:
    """Case-insensitive substring match, with the term escaped so it's
    matched literally rather than interpreted as a regex pattern."""
    return {"$regex": re.escape(value), "$options": "i"}


@app.get("/api/sources", response_model=list[str])
def list_sources():
    return sorted(s for s in get_collection().distinct("source") if s)


@app.get("/api/articles", response_model=ArticlePage)
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, min_length=1),
    source: str | None = Query(None),
    title: str | None = Query(None, min_length=1),
    body: str | None = Query(None, min_length=1),
    persons: str | None = Query(None, min_length=1),
    organizations: str | None = Query(None, min_length=1),
    locations: str | None = Query(None, min_length=1),
    dates_times: str | None = Query(None, min_length=1),
    quantities_percentages: str | None = Query(None, min_length=1),
    sentiment: str | None = Query(None, pattern="^(positive|neutral|negative)$"),
    order: str = Query("newest", pattern="^(newest|oldest)$"),
):
    collection = get_collection()
    query: dict = {}
    if q:
        query["$text"] = {"$search": q}
    if source:
        query["source"] = source
    if title:
        query["title"] = _contains(title)
    if body:
        query["body"] = _contains(body)
    if persons:
        query["entities.persons"] = _contains(persons)
    if organizations:
        query["entities.organizations"] = _contains(organizations)
    if locations:
        query["entities.locations"] = _contains(locations)
    if dates_times:
        query["entities.dates_times"] = _contains(dates_times)
    if quantities_percentages:
        query["entities.quantities_percentages"] = _contains(quantities_percentages)
    if sentiment == "positive":
        query["sentiment.compound"] = {"$gte": 0.05}
    elif sentiment == "negative":
        query["sentiment.compound"] = {"$lte": -0.05}
    elif sentiment == "neutral":
        query["sentiment.compound"] = {"$gt": -0.05, "$lt": 0.05}

    total = collection.count_documents(query)
    skip = (page - 1) * page_size

    sort_direction = -1 if order == "newest" else 1
    cursor = (
        collection.find(query)
        .sort("creation_date", sort_direction)
        .skip(skip)
        .limit(page_size)
    )
    items = [_to_article(doc) for doc in cursor]

    total_pages = (total + page_size - 1) // page_size if total else 0

    return ArticlePage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@app.get("/api/articles/{article_id}", response_model=Article)
def get_article(article_id: str):
    try:
        object_id = ObjectId(article_id)
    except InvalidId:
        logger.warning("Article lookup failed: invalid id %r", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    doc = get_collection().find_one({"_id": object_id})
    if not doc:
        logger.warning("Article lookup failed: no article with id %s", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    return _to_article(doc)


def _overlap_score(field: str, source_values: list[str], weight: float) -> dict:
    """Weight * number of values `field` shares with `source_values`."""
    return {
        "$multiply": [
            weight,
            {"$size": {"$setIntersection": [{"$ifNull": [f"${field}", []]}, source_values]}},
        ]
    }


@app.get("/api/articles/{article_id}/related", response_model=list[Article])
def get_related_articles(article_id: str, limit: int = Query(5, ge=1, le=20)):
    try:
        object_id = ObjectId(article_id)
    except InvalidId:
        logger.warning("Related-articles lookup failed: invalid id %r", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    collection = get_collection()
    source = collection.find_one({"_id": object_id})
    if not source:
        logger.warning("Related-articles lookup failed: no article with id %s", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    source_entities = source.get("entities") or {}
    source_topic = source.get("predicted_topic")
    source_topics = source.get("topics") or []
    source_persons = source_entities.get("persons") or []
    source_organizations = source_entities.get("organizations") or []
    source_locations = source_entities.get("locations") or []
    source_dates_times = source_entities.get("dates_times") or []
    source_quantities = source_entities.get("quantities_percentages") or []
    source_compound = (source.get("sentiment") or {}).get("compound")

    # Entities/topic are the substantive signal an article must share at
    # least one of to qualify as "related" -- sentiment closeness alone
    # (added below) is too weak/generic to justify a match by itself.
    entity_score = {
        "$add": [
            {"$cond": [{"$eq": ["$predicted_topic", source_topic]}, 3, 0]},
            _overlap_score("entities.persons", source_persons, 2),
            _overlap_score("entities.organizations", source_organizations, 2),
            _overlap_score("entities.locations", source_locations, 1.5),
            _overlap_score("topics", source_topics, 1),
            _overlap_score("entities.dates_times", source_dates_times, 0.5),
            _overlap_score("entities.quantities_percentages", source_quantities, 0.5),
        ]
    }

    sentiment_bonus = 0
    if source_compound is not None:
        sentiment_bonus = {
            "$multiply": [
                0.5,
                {
                    "$subtract": [
                        1,
                        {"$divide": [{"$abs": {"$subtract": ["$sentiment.compound", source_compound]}}, 2]},
                    ]
                },
            ]
        }

    pipeline = [
        {"$match": {"_id": {"$ne": object_id}}},
        {"$addFields": {"_entity_score": entity_score}},
        {"$match": {"_entity_score": {"$gt": 0}}},
        {"$addFields": {"_score": {"$add": ["$_entity_score", sentiment_bonus]}}},
        {"$sort": {"_score": -1, "creation_date": -1}},
        {"$limit": limit},
    ]

    docs = collection.aggregate(pipeline)
    return [_to_article(doc) for doc in docs]


@app.put("/api/articles/{article_id}/save", response_model=Article)
def set_article_saved(article_id: str, saved: bool = Query(...)):
    try:
        object_id = ObjectId(article_id)
    except InvalidId:
        logger.warning("Save toggle failed: invalid id %r", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    collection = get_collection()
    doc = collection.find_one_and_update(
        {"_id": object_id},
        {"$set": {"saved": saved}},
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        logger.warning("Save toggle failed: no article with id %s", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    return _to_article(doc)


@app.get("/api/saved", response_model=list[Article])
def list_saved():
    cursor = get_collection().find({"saved": True}).sort("creation_date", -1)
    return [_to_article(doc) for doc in cursor]


def _group_counts(collection, field: str) -> list[CountItem]:
    pipeline = [
        {"$match": {field: {"$exists": True, "$ne": None}}},
        {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    return [CountItem(label=str(doc["_id"]), count=doc["count"]) for doc in collection.aggregate(pipeline)]


def _top_entities(collection, field: str, limit: int = 10) -> list[EntityCount]:
    pipeline = [
        {"$unwind": f"${field}"},
        {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    return [EntityCount(value=doc["_id"], count=doc["count"]) for doc in collection.aggregate(pipeline)]


@app.get("/api/stats", response_model=Stats)
def get_stats():
    collection = get_collection()

    sentiment_counts = [
        CountItem(label="positive", count=collection.count_documents({"sentiment.compound": {"$gte": 0.05}})),
        CountItem(
            label="neutral",
            count=collection.count_documents({"sentiment.compound": {"$gt": -0.05, "$lt": 0.05}}),
        ),
        CountItem(label="negative", count=collection.count_documents({"sentiment.compound": {"$lte": -0.05}})),
    ]

    return Stats(
        total_articles=collection.count_documents({}),
        topics=_group_counts(collection, "predicted_topic"),
        sources=_group_counts(collection, "source"),
        sentiment=sentiment_counts,
        top_persons=_top_entities(collection, "entities.persons"),
        top_organizations=_top_entities(collection, "entities.organizations"),
        top_locations=_top_entities(collection, "entities.locations"),
    )

import csv
import io
import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pymongo import ReturnDocument

from db import DELETED_URLS_COLLECTION, PIPELINE_RUNS_COLLECTION, ensure_indexes, get_collection
from models import (
    Article,
    ArticlePage,
    CountItem,
    CrossSourceMatch,
    DailySentimentCount,
    EntityCount,
    PipelineRun,
    Sentiment,
    Stats,
    TopicTrendPoint,
)
from scheduler import start_scheduler, trigger_manual_run

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


app = FastAPI(title="SmartNews API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["GET", "PUT", "POST", "DELETE"],
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


@app.get("/api/topics", response_model=list[str])
def list_topics():
    return sorted(t for t in get_collection().distinct("predicted_topic") if t)


def _build_article_query(
    q: str | None,
    source: str | None,
    predicted_topic: str | None,
    title: str | None,
    body: str | None,
    persons: str | None,
    organizations: str | None,
    locations: str | None,
    dates_times: str | None,
    quantities_percentages: str | None,
    sentiment: str | None,
) -> dict:
    query: dict = {}
    if q:
        query["$text"] = {"$search": q}
    if source:
        query["source"] = source
    if predicted_topic:
        query["predicted_topic"] = predicted_topic
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
    return query


@app.get("/api/articles", response_model=ArticlePage)
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, min_length=1),
    source: str | None = Query(None),
    predicted_topic: str | None = Query(None),
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
    query = _build_article_query(
        q, source, predicted_topic, title, body, persons, organizations, locations, dates_times, quantities_percentages, sentiment
    )

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


_EXPORT_COLUMNS = [
    "id",
    "title",
    "source",
    "author_name",
    "author_link",
    "publish_date",
    "creation_date",
    "predicted_topic",
    "topics",
    "sentiment",
    "sentiment_compound",
    "sentiment_negative",
    "sentiment_neutral",
    "sentiment_positive",
    "persons",
    "organizations",
    "locations",
    "dates_times",
    "quantities_percentages",
    "saved",
    "url",
    "body",
]


def _sentiment_label(compound: float | None) -> str:
    if compound is None:
        return ""
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


# Leading characters that Excel/Sheets/LibreOffice interpret as the start of
# a formula when a CSV cell is opened -- scraped article content (title,
# body, entity text, ...) isn't fully trusted, so any cell starting with one
# of these must be neutralized before being written out.
_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: str) -> str:
    if value.startswith(_FORMULA_TRIGGER_CHARS):
        return "'" + value
    return value


def _export_rows(cursor):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_EXPORT_COLUMNS)
    yield buffer.getvalue()

    for doc in cursor:
        buffer.seek(0)
        buffer.truncate(0)
        entities = doc.get("entities") or {}
        author = doc.get("author") or {}
        sentiment = doc.get("sentiment") or {}
        compound = sentiment.get("compound")
        writer.writerow(
            [
                str(doc["_id"]),
                _csv_safe(doc.get("title") or ""),
                _csv_safe(doc.get("source") or ""),
                _csv_safe(author.get("name") or ""),
                _csv_safe(author.get("link") or ""),
                _csv_safe(doc.get("publish_date") or ""),
                _csv_safe(doc.get("creation_date") or ""),
                _csv_safe(doc.get("predicted_topic") or ""),
                _csv_safe("; ".join(doc.get("topics") or [])),
                _sentiment_label(compound),
                compound if compound is not None else "",
                sentiment.get("neg") if sentiment.get("neg") is not None else "",
                sentiment.get("neu") if sentiment.get("neu") is not None else "",
                sentiment.get("pos") if sentiment.get("pos") is not None else "",
                _csv_safe("; ".join(entities.get("persons") or [])),
                _csv_safe("; ".join(entities.get("organizations") or [])),
                _csv_safe("; ".join(entities.get("locations") or [])),
                _csv_safe("; ".join(entities.get("dates_times") or [])),
                _csv_safe("; ".join(entities.get("quantities_percentages") or [])),
                "true" if doc.get("saved") else "false",
                _csv_safe(doc.get("url") or ""),
                _csv_safe(doc.get("body") or ""),
            ]
        )
        yield buffer.getvalue()


@app.get("/api/articles/export")
def export_articles(
    q: str | None = Query(None, min_length=1),
    source: str | None = Query(None),
    predicted_topic: str | None = Query(None),
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
    query = _build_article_query(
        q, source, predicted_topic, title, body, persons, organizations, locations, dates_times, quantities_percentages, sentiment
    )
    sort_direction = -1 if order == "newest" else 1
    cursor = collection.find(query).sort("creation_date", sort_direction)

    return StreamingResponse(
        _export_rows(cursor),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=articles.csv"},
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


@app.delete("/api/articles/{article_id}", status_code=204)
def delete_article(article_id: str):
    try:
        object_id = ObjectId(article_id)
    except InvalidId:
        logger.warning("Article delete failed: invalid id %r", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    doc = get_collection().find_one_and_delete({"_id": object_id})
    if not doc:
        logger.warning("Article delete failed: no article with id %s", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    # Remember the URL so the scraper doesn't bring the article back.
    if doc.get("url"):
        get_collection(DELETED_URLS_COLLECTION).update_one(
            {"url": doc["url"]},
            {"$set": {"url": doc["url"], "deleted_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    logger.info("Deleted article %s (%s)", article_id, doc.get("url"))
    return Response(status_code=204)


def _overlap_score(field: str, source_values: list[str], weight: float) -> dict:
    """Weight * number of values `field` shares with `source_values`."""
    return {
        "$multiply": [
            weight,
            {"$size": {"$setIntersection": [{"$ifNull": [f"${field}", []]}, source_values]}},
        ]
    }


def _entity_score_expr(source: dict) -> dict:
    """How much another document's entities/topic overlap with `source`'s --
    the substantive signal two articles must share at least some of to be
    considered the same/a related story."""
    source_entities = source.get("entities") or {}
    return {
        "$add": [
            {"$cond": [{"$eq": ["$predicted_topic", source.get("predicted_topic")]}, 3, 0]},
            _overlap_score("entities.persons", source_entities.get("persons") or [], 2),
            _overlap_score("entities.organizations", source_entities.get("organizations") or [], 2),
            _overlap_score("entities.locations", source_entities.get("locations") or [], 1.5),
            _overlap_score("topics", source.get("topics") or [], 1),
            _overlap_score("entities.dates_times", source_entities.get("dates_times") or [], 0.5),
            _overlap_score(
                "entities.quantities_percentages", source_entities.get("quantities_percentages") or [], 0.5
            ),
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

    entity_score = _entity_score_expr(source)
    source_compound = (source.get("sentiment") or {}).get("compound")

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


# Stricter than the >0 threshold used for generic "related articles" --
# cross-source comparison should only surface genuine same-story matches
# (e.g. topic match plus a shared person/organization), not loosely related ones.
CROSS_SOURCE_THRESHOLD = 5


def _to_cross_source_match(doc: dict, is_current: bool) -> CrossSourceMatch:
    return CrossSourceMatch(
        article_id=str(doc["_id"]),
        source=doc.get("source"),
        title=doc.get("title"),
        url=doc.get("url"),
        sentiment=Sentiment(**doc["sentiment"]) if doc.get("sentiment") else None,
        is_current=is_current,
    )


@app.get("/api/articles/{article_id}/cross-source", response_model=list[CrossSourceMatch])
def get_cross_source_matches(article_id: str):
    try:
        object_id = ObjectId(article_id)
    except InvalidId:
        logger.warning("Cross-source lookup failed: invalid id %r", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    collection = get_collection()
    source = collection.find_one({"_id": object_id})
    if not source:
        logger.warning("Cross-source lookup failed: no article with id %s", article_id)
        raise HTTPException(status_code=404, detail="Article not found")

    matches = [_to_cross_source_match(source, is_current=True)]

    if not source.get("source"):
        return matches

    entity_score = _entity_score_expr(source)
    pipeline = [
        {"$match": {"_id": {"$ne": object_id}, "source": {"$ne": source.get("source")}}},
        {"$addFields": {"_entity_score": entity_score}},
        {"$match": {"_entity_score": {"$gte": CROSS_SOURCE_THRESHOLD}}},
        {"$sort": {"source": 1, "_entity_score": -1}},
        {"$group": {"_id": "$source", "doc": {"$first": "$$ROOT"}, "score": {"$first": "$_entity_score"}}},
        {"$sort": {"score": -1}},
    ]

    for row in collection.aggregate(pipeline):
        matches.append(_to_cross_source_match(row["doc"], is_current=False))

    return matches


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


def _daily_sentiment_trend(collection, days: int = 30) -> list[DailySentimentCount]:
    """Article counts per day (by creation_date, i.e. when scraped) for the
    last `days`, split by sentiment bucket, for the stats-page trend chart."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    pipeline = [
        {"$match": {"creation_date": {"$gte": cutoff}, "sentiment.compound": {"$exists": True}}},
        {
            "$group": {
                "_id": {"$substrCP": ["$creation_date", 0, 10]},
                "positive": {"$sum": {"$cond": [{"$gte": ["$sentiment.compound", 0.05]}, 1, 0]}},
                "negative": {"$sum": {"$cond": [{"$lte": ["$sentiment.compound", -0.05]}, 1, 0]}},
                "neutral": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$gt": ["$sentiment.compound", -0.05]},
                                    {"$lt": ["$sentiment.compound", 0.05]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"_id": 1}},
    ]
    return [
        DailySentimentCount(date=doc["_id"], positive=doc["positive"], neutral=doc["neutral"], negative=doc["negative"])
        for doc in collection.aggregate(pipeline)
    ]


def _daily_topic_trend(collection, days: int = 30, top_n: int = 6) -> list[TopicTrendPoint]:
    """Per-day article counts (by creation_date) for the `top_n` most common
    topics over the last `days`, zero-filled across every day/topic combo so
    the stats-page trend chart's lines all share the same x-axis."""
    now = datetime.now(timezone.utc)
    date_keys = [(now - timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(days - 1, -1, -1)]
    cutoff = (now - timedelta(days=days)).isoformat()

    top_topics = [
        doc["_id"]
        for doc in collection.aggregate(
            [
                {"$match": {"creation_date": {"$gte": cutoff}, "predicted_topic": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$predicted_topic", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": top_n},
            ]
        )
    ]
    if not top_topics:
        return []

    pipeline = [
        {"$match": {"creation_date": {"$gte": cutoff}, "predicted_topic": {"$in": top_topics}}},
        {
            "$group": {
                "_id": {"date": {"$substrCP": ["$creation_date", 0, 10]}, "topic": "$predicted_topic"},
                "count": {"$sum": 1},
            }
        },
    ]
    counts = {(doc["_id"]["date"], doc["_id"]["topic"]): doc["count"] for doc in collection.aggregate(pipeline)}

    return [
        TopicTrendPoint(date=date, topic=topic, count=counts.get((date, topic), 0))
        for date in date_keys
        for topic in top_topics
    ]


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
        sentiment_trend=_daily_sentiment_trend(collection),
        topic_trend=_daily_topic_trend(collection),
    )


def _to_pipeline_run(doc: dict) -> PipelineRun:
    doc["id"] = str(doc.pop("_id"))
    return PipelineRun(**doc)


@app.get("/api/pipeline/runs", response_model=list[PipelineRun])
def list_pipeline_runs(limit: int = Query(20, ge=1, le=100)):
    cursor = get_collection(PIPELINE_RUNS_COLLECTION).find().sort("started_at", -1).limit(limit)
    return [_to_pipeline_run(doc) for doc in cursor]


@app.post("/api/pipeline/run")
def trigger_pipeline_run():
    if not trigger_manual_run():
        raise HTTPException(status_code=409, detail="A pipeline run is already in progress")
    return {"status": "started"}

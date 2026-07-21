from contextlib import asynccontextmanager
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from db import ensure_indexes, get_collection
from models import Article, ArticlePage
from scheduler import start_scheduler

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_indexes()
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(title="NLP Scraper API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _to_article(doc: dict) -> Article:
    doc["id"] = str(doc.pop("_id"))
    return Article(**doc)


@app.get("/api/articles", response_model=ArticlePage)
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, min_length=1),
):
    collection = get_collection()
    query = {"$text": {"$search": q}} if q else {}

    total = collection.count_documents(query)
    skip = (page - 1) * page_size

    cursor = (
        collection.find(query)
        .sort("publish_date", -1)
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
        raise HTTPException(status_code=404, detail="Article not found")

    doc = get_collection().find_one({"_id": object_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")

    return _to_article(doc)

from pydantic import BaseModel


class Author(BaseModel):
    name: str | None = None
    link: str | None = None


class Entities(BaseModel):
    persons: list[str] = []
    organizations: list[str] = []
    locations: list[str] = []
    dates_times: list[str] = []
    quantities_percentages: list[str] = []


class Sentiment(BaseModel):
    neg: float = 0.0
    neu: float = 0.0
    pos: float = 0.0
    compound: float = 0.0


class Article(BaseModel):
    id: str
    creation_date: str | None = None
    publish_date: str | None = None
    title: str | None = None
    body: str | None = None
    entities: Entities | None = None
    sentiment: Sentiment | None = None
    topics: list[str] = []
    predicted_topic: str | None = None
    author: Author
    url: str | None = None
    source: str | None = None
    saved: bool = False


class ArticlePage(BaseModel):
    items: list[Article]
    page: int
    page_size: int
    total: int
    total_pages: int


class CountItem(BaseModel):
    label: str
    count: int


class EntityCount(BaseModel):
    value: str
    count: int


class DailySentimentCount(BaseModel):
    date: str
    positive: int
    neutral: int
    negative: int


class PipelineRun(BaseModel):
    id: str
    started_at: str
    finished_at: str | None = None
    status: str  # "running" | "success" | "failed"
    trigger: str  # "scheduled" | "manual"
    output: str | None = None
    error: str | None = None


class CrossSourceMatch(BaseModel):
    article_id: str
    source: str | None = None
    title: str | None = None
    url: str | None = None
    sentiment: Sentiment | None = None
    is_current: bool = False


class Stats(BaseModel):
    total_articles: int
    topics: list[CountItem]
    sources: list[CountItem]
    sentiment: list[CountItem]
    top_persons: list[EntityCount]
    top_organizations: list[EntityCount]
    top_locations: list[EntityCount]
    sentiment_trend: list[DailySentimentCount]

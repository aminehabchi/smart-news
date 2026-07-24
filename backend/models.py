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


class Stats(BaseModel):
    total_articles: int
    topics: list[CountItem]
    sources: list[CountItem]
    sentiment: list[CountItem]
    top_persons: list[EntityCount]
    top_organizations: list[EntityCount]
    top_locations: list[EntityCount]

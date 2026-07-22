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


class Article(BaseModel):
    id: str
    creation_date: str | None = None
    publish_date: str | None = None
    title: str | None = None
    body: str | None = None
    entities: Entities | None = None
    topics: list[str] = []
    author: Author
    url: str | None = None
    source: str | None = None


class ArticlePage(BaseModel):
    items: list[Article]
    page: int
    page_size: int
    total: int
    total_pages: int

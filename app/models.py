from pydantic import BaseModel


class Author(BaseModel):
    name: str | None = None
    link: str | None = None


class Article(BaseModel):
    id: str
    creation_date: str | None = None
    publish_date: str | None = None
    title: str | None = None
    body: str | None = None
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

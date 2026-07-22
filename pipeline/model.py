from pydantic import BaseModel


class Author(BaseModel):
    name: str | None = None
    link: str | None = None


class Article(BaseModel):
    id: str | None = None
    creation_date: str | None = None
    publish_date: str | None = None
    title: str | None = None
    body: str | None = None
    clean_text: str | None = None
    topics: list[str] = []
    author: Author
    url: str | None = None
    source: str | None = None

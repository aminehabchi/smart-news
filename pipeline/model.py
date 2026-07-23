from pydantic import BaseModel


class Author(BaseModel):
    name: str | None = None
    link: str | None = None


class Preprocessing(BaseModel):
    """Output of each stage of the NLP preprocessing pipeline (see text_preprocessing/preprocessing.py:preprocess_text)."""

    lowercased: str | None = None
    no_punctuation: str | None = None
    sentences: list[str] = []
    word_tokens: list[str] = []
    tokens_no_stopwords: list[str] = []
    stemmed_tokens: list[str] = []
    # Each stemmed token represented numerically as its integer id in the
    # run's corpus vocabulary (see text_preprocessing/bow.py:tokens_to_ids).
    token_ids: list[int] = []


class Entities(BaseModel):
    """Named entities extracted from an article (see nlp_engine/ner.py:extract_entities)."""

    persons: list[str] = []
    organizations: list[str] = []
    locations: list[str] = []
    dates_times: list[str] = []
    quantities_percentages: list[str] = []


class Article(BaseModel):
    id: str | None = None
    creation_date: str | None = None
    publish_date: str | None = None
    title: str | None = None
    body: str | None = None
    clean_text: str | None = None
    preprocessing: Preprocessing | None = None
    entities: Entities | None = None
    topics: list[str] = []
    # Single predicted category (business/entertainment/politics/sport/tech),
    # see topic_classifier/orchestrator.py. Distinct from `topics` above,
    # which are free-form tags/keywords scraped from the source site.
    predicted_topic: str | None = None
    author: Author
    url: str | None = None
    source: str | None = None

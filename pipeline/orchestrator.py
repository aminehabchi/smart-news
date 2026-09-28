"""Entry point: scrape the latest articles from all sources, clean them, run
NER, sentiment analysis, and topic classification on them, and store them in
MongoDB.

NER, sentiment analysis, and topic classification also run separately over
historical articles via pipeline/nlp_engine/orchestrator.py,
pipeline/nlp_engine/sentiment_orchestrator.py, and
topic_classifier/orchestrator.py (self-tracking backfill scripts) -- this
module runs the same steps inline so freshly scraped articles are fully
processed in one pass.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
from dotenv import load_dotenv

from db import get_deleted_urls, insert_articles, insert_word_frequencies
from model import Article
from nlp_engine.ner import extract_entities
from nlp_engine.sentiment import analyze_sentiment
from scrapers import arstechnica, techcrunch, theverge
from text_preprocessing.bow import fit_corpus_vectorizer, tokens_to_ids, word_frequencies
from text_preprocessing.preprocessing import clean_article

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger("orchestrator")

# Max articles to scrape from each source per run.
SCRAPER_LIMIT = int(os.getenv("SCRAPER_LIMIT", "20"))

SCRAPERS = [techcrunch, theverge, arstechnica]

TOPIC_MODEL_PATH = Path(__file__).resolve().parent / "topic_classifier" / "model" / "topic_classifier.pkl"


def predict_topic(article: Article, vectorizer, model) -> str | None:
    tokens = article.preprocessing.stemmed_tokens if article.preprocessing else []
    if not tokens:
        return None
    features = vectorizer.transform([" ".join(tokens)])
    return str(model.predict(features)[0])


def main() -> None:
    topic_vectorizer = topic_model = None
    if TOPIC_MODEL_PATH.exists():
        saved = joblib.load(TOPIC_MODEL_PATH)
        topic_vectorizer, topic_model = saved["vectorizer"], saved["model"]
    else:
        logger.warning("No trained topic classifier at %s, skipping topic prediction.", TOPIC_MODEL_PATH)

    deleted_urls = get_deleted_urls()

    total = 0
    batches: list[tuple[str, list[Article]]] = []
    all_articles: list[Article] = []

    for scraper in SCRAPERS:
        try:
            raw_articles = scraper.scrape_latest(limit=SCRAPER_LIMIT)
            raw_articles = [data for data in raw_articles if data.get("url") not in deleted_urls]
            articles = [clean_article(Article(**data)) for data in raw_articles]
        except Exception:
            logger.error("%s: scraping failed, skipping this source.", scraper.SOURCE, exc_info=True)
            continue

        for article in articles:
            article.entities = extract_entities(article)
            article.sentiment = analyze_sentiment(article)
            if topic_vectorizer is not None:
                article.predicted_topic = predict_topic(article, topic_vectorizer, topic_model)

        batches.append((scraper.SOURCE, articles))
        all_articles.extend(articles)
        total += len(articles)

    # The token -> id vocabulary and word frequencies are corpus-wide, so
    # they're built once the whole run's articles are known, before storing.
    vectorizer = fit_corpus_vectorizer(
        [article.preprocessing.stemmed_tokens for article in all_articles if article.preprocessing]
    )
    if vectorizer is not None:
        for article in all_articles:
            if article.preprocessing:
                article.preprocessing.token_ids = tokens_to_ids(
                    article.preprocessing.stemmed_tokens, vectorizer
                )

    for source, articles in batches:
        insert_articles(articles)
        logger.info("%s: inserted/updated %d articles.", source, len(articles))

    frequencies = (
        word_frequencies(
            vectorizer,
            [article.preprocessing.stemmed_tokens for article in all_articles if article.preprocessing],
        )
        if vectorizer is not None
        else {}
    )
    insert_word_frequencies(
        {
            "run_date": datetime.now(timezone.utc).isoformat(),
            "sources": [source for source, _ in batches],
            "article_count": total,
            "word_frequencies": frequencies,
        }
    )
    top_words = list(frequencies.items())[:10]

    logger.info("Done. %d articles processed. Top words: %s", total, top_words)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main()

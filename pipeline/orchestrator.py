"""Entry point: scrape the latest articles from all sources, clean them, and store them in MongoDB."""

from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from db import insert_articles, insert_word_frequencies
from model import Article
from scrapers import arstechnica, techcrunch, theverge
from text_preprocessing.bow import fit_corpus_vectorizer, tokens_to_ids, word_frequencies
from text_preprocessing.preprocessing import clean_article

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SCRAPERS = [techcrunch, theverge, arstechnica]


def main() -> None:
    total = 0
    batches: list[tuple[str, list[Article]]] = []
    all_articles: list[Article] = []

    for scraper in SCRAPERS:
        raw_articles = scraper.scrape_latest(limit=20)
        articles = [clean_article(Article(**data)) for data in raw_articles]
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
        print(f"{source}: inserted/updated {len(articles)} articles.")

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
            "sources": [scraper.SOURCE for scraper in SCRAPERS],
            "article_count": total,
            "word_frequencies": frequencies,
        }
    )
    top_words = list(frequencies.items())[:10]

    print(f"Done. {total} articles processed. Top words: {top_words}")


if __name__ == "__main__":
    main()

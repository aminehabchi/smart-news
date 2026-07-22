"""Entry point: scrape the latest articles from all sources, clean them, and store them in MongoDB."""

from pathlib import Path

from dotenv import load_dotenv

from cleaner.text_cleaner import clean_article
from db import insert_articles
from model import Article
from scrapers import arstechnica, techcrunch, theverge

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SCRAPERS = [techcrunch, theverge, arstechnica]


def main() -> None:
    total = 0
    for scraper in SCRAPERS:
        raw_articles = scraper.scrape_latest(limit=20)
        articles = [clean_article(Article(**data)) for data in raw_articles]
        insert_articles(articles)
        total += len(articles)
        print(f"{scraper.SOURCE}: inserted/updated {len(articles)} articles.")

    print(f"Done. {total} articles processed.")


if __name__ == "__main__":
    main()

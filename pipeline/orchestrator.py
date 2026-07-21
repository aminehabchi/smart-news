"""Entry point: scrape the latest TechCrunch articles and store them in MongoDB."""

from pathlib import Path

from dotenv import load_dotenv

from db import insert_articles
from scrapers.techcrunch import scrape_latest

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def main() -> None:
    articles = scrape_latest(limit=20)
    insert_articles(articles)
    print(f"Inserted/updated {len(articles)} articles.")


if __name__ == "__main__":
    main()

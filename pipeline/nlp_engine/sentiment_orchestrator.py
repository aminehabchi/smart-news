"""Entry point: run sentiment analysis over every article that doesn't have
`sentiment` yet and store the result.

Run separately from pipeline/orchestrator.py (its own run.sh); self-tracking
via the `sentiment` field, so each run only picks up articles no prior run
(of this or any nlp_engine stage) has processed yet.
"""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nlp_engine.sentiment_orchestrator")

from dotenv import load_dotenv  # noqa: E402

from db import get_collection  # noqa: E402
from model import Article  # noqa: E402
from nlp_engine.sentiment import analyze_sentiment  # noqa: E402 -- logs at import time (VADER lexicon load), so basicConfig above must run first

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def main() -> None:
    collection = get_collection()
    cursor = collection.find({"sentiment": {"$exists": False}})

    processed = 0
    for doc in cursor:
        object_id = doc["_id"]
        doc["id"] = str(doc.pop("_id"))
        article = Article(**doc)

        sentiment = analyze_sentiment(article)
        collection.update_one(
            {"_id": object_id},
            {"$set": {"sentiment": sentiment.model_dump()}},
        )
        processed += 1

    logger.info("Sentiment: updated %d articles.", processed)


if __name__ == "__main__":
    main()

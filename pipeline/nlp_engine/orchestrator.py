"""Entry point: run NER over every article that doesn't have `entities` yet and store the result.

Run separately from pipeline/orchestrator.py (its own run.sh); self-tracking
via the `entities` field, so each run only picks up articles no prior run
(of this or any nlp_engine stage) has processed yet.
"""

from pathlib import Path

from dotenv import load_dotenv

from db import get_collection
from model import Article
from nlp_engine.ner import extract_entities

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def main() -> None:
    collection = get_collection()
    cursor = collection.find({"entities": {"$exists": False}})

    processed = 0
    for doc in cursor:
        object_id = doc["_id"]
        doc["id"] = str(doc.pop("_id"))
        article = Article(**doc)

        entities = extract_entities(article)
        collection.update_one(
            {"_id": object_id},
            {"$set": {"entities": entities.model_dump()}},
        )
        processed += 1

    print(f"NER: updated {processed} articles.")


if __name__ == "__main__":
    main()

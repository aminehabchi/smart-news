"""Entry point: predict each article's topic category using the trained
classifier (model/topic_classifier.pkl) and store it as `predicted_topic`.

This is a backfill script for articles that predate/missed inline topic
prediction in pipeline/orchestrator.py; self-tracking via the
`predicted_topic` field, so each run only picks up articles no prior run has
classified yet -- same pattern as pipeline/nlp_engine/orchestrator.py (NER).

Reuses the article's already-computed preprocessing.stemmed_tokens (see
pipeline/text_preprocessing/preprocessing.py) rather than re-cleaning text,
since that's exactly the representation the model was trained on (see
training/prepare_data.py) -- guarantees identical cleaning between training
and inference without duplicating the cleaning code here.
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("topic_classifier.orchestrator")

import joblib  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

TOPIC_CLASSIFIER_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = TOPIC_CLASSIFIER_DIR.parent
MODEL_PATH = TOPIC_CLASSIFIER_DIR / "model" / "topic_classifier.pkl"

# topic_classifier lives inside pipeline/ and shares its venv, but this
# script is run with topic_classifier/ as the cwd (see classify.sh), so
# pipeline/ still needs to be added to sys.path to reuse its Mongo access
# and Article model rather than duplicating them.
sys.path.insert(0, str(PIPELINE_DIR))

from db import get_collection  # noqa: E402
from model import Article  # noqa: E402

load_dotenv(PIPELINE_DIR.parent / ".env")


def main() -> None:
    saved = joblib.load(MODEL_PATH)
    vectorizer, model = saved["vectorizer"], saved["model"]

    collection = get_collection()
    cursor = collection.find(
        {
            "predicted_topic": {"$exists": False},
            "preprocessing.stemmed_tokens": {"$exists": True, "$ne": []},
        }
    )

    processed = 0
    for doc in cursor:
        object_id = doc["_id"]
        doc["id"] = str(doc.pop("_id"))
        article = Article(**doc)

        text = " ".join(article.preprocessing.stemmed_tokens)
        features = vectorizer.transform([text])
        predicted_topic = str(model.predict(features)[0])

        collection.update_one(
            {"_id": object_id},
            {"$set": {"predicted_topic": predicted_topic}},
        )
        processed += 1

    logger.info("Topic classifier: updated %d articles.", processed)


if __name__ == "__main__":
    main()

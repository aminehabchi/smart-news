"""Evaluates the trained topic classifier (model/topic_classifier.pkl) against
the held-out data/test.csv and prints accuracy, a per-class classification
report, and a confusion matrix.
"""

import csv
import logging
from pathlib import Path

import joblib
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

logger = logging.getLogger("topic_classifier.evaluate")

TOPIC_CLASSIFIER_DIR = Path(__file__).resolve().parent.parent
TEST_PATH = TOPIC_CLASSIFIER_DIR / "data" / "test.csv"
MODEL_PATH = TOPIC_CLASSIFIER_DIR / "model" / "topic_classifier.pkl"


def load_dataset(path: Path) -> tuple[list[str], list[str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [row["text"] for row in rows], [row["category"] for row in rows]


def main() -> None:
    texts, labels = load_dataset(TEST_PATH)

    saved = joblib.load(MODEL_PATH)
    vectorizer, model = saved["vectorizer"], saved["model"]

    features = vectorizer.transform(texts)
    predictions = model.predict(features)

    logger.info("Accuracy: %.3f", accuracy_score(labels, predictions))
    logger.info("Classification report:\n%s", classification_report(labels, predictions))
    logger.info(
        "Confusion matrix (rows=actual, cols=predicted, labels=%s):\n%s",
        model.classes_,
        confusion_matrix(labels, predictions, labels=model.classes_),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main()

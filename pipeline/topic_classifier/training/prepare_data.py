"""Cleans the raw BBC News train/test CSVs (data/raw_train.csv, data/raw_test.csv)
using the same text cleaning as the article pipeline (see
text_preprocessing/preprocessing.py: clean_text + preprocess_text), and
writes the result to data/train.csv and data/test.csv as (text, category)
pairs -- text is the article's stemmed, stopword-free tokens, space-joined,
matching what the article pipeline reduces each article to before it's
represented numerically.
"""

import csv
import logging
import sys
from pathlib import Path

logger = logging.getLogger("topic_classifier.prepare_data")

TOPIC_CLASSIFIER_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = TOPIC_CLASSIFIER_DIR / "data"

# topic_classifier lives outside pipeline/, but reuses its article cleaning
# code rather than duplicating it -- so pipeline/ is added to the import
# path explicitly instead of relying on cwd (as pipeline's own scripts do).
sys.path.insert(0, str(TOPIC_CLASSIFIER_DIR.parent / "pipeline"))

from text_preprocessing.preprocessing import clean_text, preprocess_text  # noqa: E402

RAW_FILES = {
    DATA_DIR / "raw_train.csv": DATA_DIR / "train.csv",
    DATA_DIR / "raw_test.csv": DATA_DIR / "test.csv",
}


def clean_dataset(raw_path: Path) -> list[dict[str, str]]:
    rows = []
    with raw_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cleaned = clean_text(row["Text"])
            stemmed_tokens = preprocess_text(cleaned).stemmed_tokens
            rows.append({"text": " ".join(stemmed_tokens), "category": row["Category"]})
    return rows


def write_dataset(rows: list[dict[str, str]], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "category"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    for raw_path, out_path in RAW_FILES.items():
        rows = clean_dataset(raw_path)
        write_dataset(rows, out_path)
        logger.info("%s -> %s: cleaned %d rows.", raw_path.name, out_path.name, len(rows))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main()

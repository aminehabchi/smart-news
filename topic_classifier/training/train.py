"""Trains the topic classifier: TF-IDF vectorizer + LogisticRegression over
data/train.csv (produced by prepare_data.py), then saves both the fitted
vectorizer and the model to model/topic_classifier.pkl, plus a learning-curve
plot (model/learning_curves.png) showing train vs. cross-validation accuracy
as training-set size grows -- a converging, close-together pair of curves
indicates the model generalizes rather than overfitting the training set.
"""

import csv
import logging
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")  # headless: this script never opens a display
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import learning_curve

logger = logging.getLogger("topic_classifier.train")

TOPIC_CLASSIFIER_DIR = Path(__file__).resolve().parent.parent
TRAIN_PATH = TOPIC_CLASSIFIER_DIR / "data" / "train.csv"
MODEL_PATH = TOPIC_CLASSIFIER_DIR / "model" / "topic_classifier.pkl"
LEARNING_CURVE_PATH = TOPIC_CLASSIFIER_DIR / "model" / "learning_curves.png"


def load_dataset(path: Path) -> tuple[list[str], list[str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [row["text"] for row in rows], [row["category"] for row in rows]


def plot_learning_curve(model: LogisticRegression, features, labels, out_path: Path) -> None:
    train_sizes, train_scores, val_scores = learning_curve(
        model,
        features,
        labels,
        cv=5,
        train_sizes=np.linspace(0.1, 1.0, 8),
        scoring="accuracy",
    )

    train_mean, train_std = train_scores.mean(axis=1), train_scores.std(axis=1)
    val_mean, val_std = val_scores.mean(axis=1), val_scores.std(axis=1)

    plt.figure(figsize=(8, 5))
    plt.plot(train_sizes, train_mean, "o-", color="tab:blue", label="Training accuracy")
    plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.15, color="tab:blue")
    plt.plot(train_sizes, val_mean, "o-", color="tab:orange", label="Cross-validation accuracy")
    plt.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.15, color="tab:orange")

    plt.title("Topic classifier learning curves")
    plt.xlabel("Training examples")
    plt.ylabel("Accuracy")
    plt.ylim(0, 1.05)
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def main() -> None:
    texts, labels = load_dataset(TRAIN_PATH)

    vectorizer = TfidfVectorizer(min_df=2, sublinear_tf=True)
    features = vectorizer.fit_transform(texts)

    model = LogisticRegression(max_iter=1000)
    model.fit(features, labels)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"vectorizer": vectorizer, "model": model}, MODEL_PATH)

    plot_learning_curve(LogisticRegression(max_iter=1000), features, labels, LEARNING_CURVE_PATH)

    train_accuracy = model.score(features, labels)
    logger.info(
        "Trained on %d articles, %d features. Train accuracy: %.3f. Saved model to %s, learning curves to %s.",
        len(texts),
        features.shape[1],
        train_accuracy,
        MODEL_PATH,
        LEARNING_CURVE_PATH,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main()

"""Sentiment analysis: scores an article's body with NLTK's VADER
(Valence Aware Dictionary and sEntiment Reasoner), a lexicon/rule-based model
that works directly on raw, unprocessed text (punctuation, capitalization,
and intensifiers all factor into its scoring), so it reads Article.body
directly rather than the cleaned/stemmed text_preprocessing output.
"""

import logging

from nltk.sentiment import SentimentIntensityAnalyzer

from model import Article, Sentiment

logger = logging.getLogger("nlp_engine.sentiment")

logger.info("Loading VADER lexicon")
_ANALYZER = SentimentIntensityAnalyzer()


def analyze_sentiment(article: Article) -> Sentiment:
    text = article.body or ""
    if not text.strip():
        return Sentiment()

    scores = _ANALYZER.polarity_scores(text)
    return Sentiment(**scores)

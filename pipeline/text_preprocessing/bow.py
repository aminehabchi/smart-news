"""Bag-of-words model over a run's articles: builds one corpus-wide vocabulary,
then uses it for both per-article numeric token encoding and overall word frequency."""

from sklearn.feature_extraction.text import CountVectorizer


def fit_corpus_vectorizer(token_lists: list[list[str]]) -> CountVectorizer | None:
    """Fits one CountVectorizer over every article's stemmed tokens in the run,
    building a shared vocabulary (token -> integer id) for the whole corpus."""
    documents = [" ".join(tokens) for tokens in token_lists if tokens]
    if not documents:
        return None

    vectorizer = CountVectorizer()
    vectorizer.fit(documents)
    return vectorizer


def tokens_to_ids(tokens: list[str], vectorizer: CountVectorizer) -> list[int]:
    """Represents each token numerically as its integer id in the corpus
    vocabulary. Tokens the vectorizer doesn't recognize (e.g. single
    characters, filtered by its default token pattern) are dropped."""
    vocabulary = vectorizer.vocabulary_
    return [vocabulary[token] for token in tokens if token in vocabulary]


def word_frequencies(
    vectorizer: CountVectorizer, token_lists: list[list[str]]
) -> dict[str, int]:
    """Feeds each article's stemmed tokens through the fitted vectorizer and
    sums counts across the corpus, returning words ordered by frequency (highest first)."""
    documents = [" ".join(tokens) for tokens in token_lists if tokens]
    if not documents:
        return {}

    matrix = vectorizer.transform(documents)
    counts = matrix.sum(axis=0).A1

    return dict(
        sorted(
            zip(vectorizer.get_feature_names_out(), counts.tolist()),
            key=lambda pair: pair[1],
            reverse=True,
        )
    )

"""Cleans raw scraped article text and runs the NLP preprocessing pipeline.

`Article.body` is left untouched (original casing/punctuation preserved,
since NER later relies on capitalization). Two derived fields are produced:

`Article.clean_text` -- character-level cleanup only (clean_text()):
  1. strip embedded citation artifacts some scrapers pick up
     (e.g. "[Link: text | url | Publisher]")
  2. unicode-normalize (NFKC)
  3. drop control/format/symbol characters (emoji, zero-width chars, etc.)
  4. normalize smart quotes/dashes/ellipsis to their plain equivalents
  5. collapse repeated whitespace and trim
  6. lowercase

`Article.preprocessing` -- NLP tokenization pipeline (preprocess_text()),
run on top of clean_text:
  1. lowercase
  2. sentence-tokenize
  3. strip punctuation
  4. word-tokenize
  5. remove stop words
  6. stem to root forms (Porter stemmer)
  7. represent each stemmed token numerically -- filled in separately by
     text_preprocessing/bow.py once the whole run's corpus is known, since
     the token -> id vocabulary is built across every article in the run
"""

import re
import string
import unicodedata

from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize

from model import Article, Preprocessing

_CITATION_RE = re.compile(r"\[Link:.*?\]", re.IGNORECASE | re.DOTALL)
_WHITESPACE_RE = re.compile(r"\s+")

# Unicode general categories dropped as "special characters": control (Cc),
# format (Cf, e.g. zero-width joiners), private-use (Co), surrogates (Cs),
# and standalone symbols (So, e.g. emoji/dingbats). Letters, digits, and all
# punctuation categories (including $, %, &, ...) are kept.
_STRIP_CATEGORIES = {"Cc", "Cf", "Co", "Cs", "So"}

_PUNCTUATION_MAP = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
    "…": "...",
    "\xa0": " ",
}

_STOPWORDS = set(stopwords.words("english"))
_STEMMER = PorterStemmer()
_PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation)


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = _CITATION_RE.sub(" ", text)
    text = unicodedata.normalize("NFKC", text)

    for smart, plain in _PUNCTUATION_MAP.items():
        text = text.replace(smart, plain)

    text = "".join(
        ch
        for ch in text
        if ch.isspace() or unicodedata.category(ch) not in _STRIP_CATEGORIES
    )
    text = _WHITESPACE_RE.sub(" ", text).strip()

    return text.lower()


def preprocess_text(text: str) -> Preprocessing:
    """Reusable NLP preprocessing pipeline: lowercase, strip punctuation,
    tokenize at sentence and word level, remove stop words, stem. Returns
    every intermediate step so it can be persisted alongside the article."""
    if not text:
        return Preprocessing()

    lowercased = text.lower()

    # Sentence boundaries depend on punctuation (".", "!", "?"), so
    # sentence-tokenize before stripping it.
    sentences = sent_tokenize(lowercased)

    no_punctuation = _WHITESPACE_RE.sub(
        " ", lowercased.translate(_PUNCTUATION_TABLE)
    ).strip()

    word_tokens = [
        token
        for sentence in sentences
        for token in word_tokenize(sentence.translate(_PUNCTUATION_TABLE))
        if token.strip()
    ]

    tokens_no_stopwords = [token for token in word_tokens if token not in _STOPWORDS]
    stemmed_tokens = [_STEMMER.stem(token) for token in tokens_no_stopwords]

    return Preprocessing(
        lowercased=lowercased,
        no_punctuation=no_punctuation,
        sentences=sentences,
        word_tokens=word_tokens,
        tokens_no_stopwords=tokens_no_stopwords,
        stemmed_tokens=stemmed_tokens,
    )


def clean_article(article: Article) -> Article:
    article.clean_text = clean_text(article.body or "")
    article.preprocessing = preprocess_text(article.clean_text)
    return article


def raw_text(article: Article) -> str:
    """Joins title, body, and topics into one string, unmodified. For
    consumers (e.g. NER) that need the original casing/punctuation intact,
    rather than the lowercased/tokenized preprocess_text() output.

    Topics are newline-separated, not space-joined: NER relies on
    boundaries between phrases, and a bare space between adjacent topic
    tags (e.g. "AI Business Google") reads as one run-on phrase."""
    parts = [article.title, article.body, *(article.topics or [])]
    return "\n".join(part for part in parts if part)

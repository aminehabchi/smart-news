"""Cleans raw scraped article text before the NLP stage.

`Article.body` is left untouched (original casing/punctuation preserved,
since NER later relies on capitalization). The cleaned result goes into the
separate `Article.clean_text` field:

  1. strip embedded citation artifacts some scrapers pick up
     (e.g. "[Link: text | url | Publisher]")
  2. unicode-normalize (NFKC)
  3. drop control/format/symbol characters (emoji, zero-width chars, etc.)
  4. normalize smart quotes/dashes/ellipsis to their plain equivalents
  5. collapse repeated whitespace and trim
  6. lowercase
"""

import re
import unicodedata

from model import Article

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


def clean_article(article: Article) -> Article:
    article.clean_text = clean_text(article.body or "")
    return article

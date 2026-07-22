"""Named Entity Recognition: extracts people, organizations, locations,
dates/times, and quantities/percentages from an article's title, body, and topics.

Runs on the original (non-lowercased) text -- capitalization is a key signal
for spaCy's NER model -- so it reads Article.title/body/topics directly
rather than the lowercased text_preprocessing output.
"""

import logging

import spacy

from model import Article, Entities
from text_preprocessing.preprocessing import raw_text

logger = logging.getLogger("nlp_engine.ner")

logger.info("Loading spaCy model en_core_web_sm")
_NLP = spacy.load("en_core_web_sm")

_LOCATION_LABELS = {"GPE", "LOC"}
_DATETIME_LABELS = {"DATE", "TIME"}
_QUANTITY_LABELS = {"PERCENT", "QUANTITY"}


def extract_entities(article: Article) -> Entities:
    text = raw_text(article)
    if not text.strip():
        return Entities()

    doc = _NLP(text)

    persons: set[str] = set()
    organizations: set[str] = set()
    locations: set[str] = set()
    dates_times: set[str] = set()
    quantities_percentages: set[str] = set()

    for ent in doc.ents:
        value = ent.text.strip()
        if not value:
            continue

        if ent.label_ == "PERSON":
            persons.add(value)
        elif ent.label_ == "ORG":
            organizations.add(value)
        elif ent.label_ in _LOCATION_LABELS:
            locations.add(value)
        elif ent.label_ in _DATETIME_LABELS:
            dates_times.add(value)
        elif ent.label_ in _QUANTITY_LABELS:
            quantities_percentages.add(value)

    return Entities(
        persons=sorted(persons),
        organizations=sorted(organizations),
        locations=sorted(locations),
        dates_times=sorted(dates_times),
        quantities_percentages=sorted(quantities_percentages),
    )

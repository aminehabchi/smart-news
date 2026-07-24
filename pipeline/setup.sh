#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
python -m nltk.downloader punkt punkt_tab stopwords vader_lexicon
python -m spacy download en_core_web_sm

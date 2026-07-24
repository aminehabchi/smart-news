#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

source venv/bin/activate
pip install -r requirements.txt
python -m nltk.downloader punkt punkt_tab stopwords

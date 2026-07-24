#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
source venv/bin/activate
python training/prepare_data.py
python training/train.py
python training/evaluate.py

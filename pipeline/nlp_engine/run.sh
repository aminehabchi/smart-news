#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
source venv/bin/activate
python -m nlp_engine.orchestrator
python -m nlp_engine.sentiment_orchestrator

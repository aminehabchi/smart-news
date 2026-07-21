#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

source venv/bin/activate
uvicorn main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}" --reload

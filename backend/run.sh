#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
source venv/bin/activate

PIDS_FILE="$(cd .. && pwd)/pids"
touch "$PIDS_FILE"
grep -v '^backend=' "$PIDS_FILE" > "$PIDS_FILE.tmp" || true
mv "$PIDS_FILE.tmp" "$PIDS_FILE"

setsid nohup uvicorn main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}" --reload \
  > backend.log 2>&1 < /dev/null &
pid=$!

echo "backend=$pid" >> "$PIDS_FILE"
echo "backend started (pid $pid), logs: backend/backend.log"

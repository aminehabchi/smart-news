#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

PIDS_FILE="$(cd .. && pwd)/pids"
touch "$PIDS_FILE"
grep -v '^frontend=' "$PIDS_FILE" > "$PIDS_FILE.tmp" || true
mv "$PIDS_FILE.tmp" "$PIDS_FILE"

setsid nohup npm start > frontend.log 2>&1 < /dev/null &
pid=$!

echo "frontend=$pid" >> "$PIDS_FILE"
echo "frontend started (pid $pid), logs: frontend/frontend.log"

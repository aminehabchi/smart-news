#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
PIDS_FILE="$(cd .. && pwd)/pids"

pid=$(grep '^backend=' "$PIDS_FILE" 2>/dev/null | cut -d= -f2)
if [ -z "$pid" ]; then
  echo "backend: no pid on record, nothing to stop."
  exit 0
fi

if kill -- "-$pid" 2>/dev/null; then
  echo "backend: stopped (pid $pid)."
else
  echo "backend: process $pid not running (already stopped?)."
fi

grep -v '^backend=' "$PIDS_FILE" > "$PIDS_FILE.tmp" || true
mv "$PIDS_FILE.tmp" "$PIDS_FILE"

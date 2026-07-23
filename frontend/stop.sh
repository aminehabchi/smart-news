#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
PIDS_FILE="$(cd .. && pwd)/pids"

pid=$(grep '^frontend=' "$PIDS_FILE" 2>/dev/null | cut -d= -f2)
if [ -z "$pid" ]; then
  echo "frontend: no pid on record, nothing to stop."
  exit 0
fi

if kill -- "-$pid" 2>/dev/null; then
  echo "frontend: stopped (pid $pid)."
else
  echo "frontend: process $pid not running (already stopped?)."
fi

grep -v '^frontend=' "$PIDS_FILE" > "$PIDS_FILE.tmp" || true
mv "$PIDS_FILE.tmp" "$PIDS_FILE"

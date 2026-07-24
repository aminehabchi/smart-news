#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

./pipeline/setup.sh
./pipeline/topic_classifier/setup.sh
./backend/setup.sh
./frontend/setup.sh

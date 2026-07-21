#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -f angular.json ]; then
  npx @angular/cli new frontend --directory=. --skip-git --package-manager=npm
fi

npm install

#!/bin/bash
set -e
docker run --rm -v "$(pwd):/src" -w /src python:3.12-alpine sh -c "pip install -q ruff && ruff check --fix --select I . && ruff format ."
docker run --rm -v "$(pwd):/src" -w /src node:alpine npx --yes prettier --write "**/*.md" "*.yml"

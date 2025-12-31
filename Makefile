.PHONY: help setup start stop restart logs status validate clean
.PHONY: format format-python format-markdown format-docker

# Default target
help:
	@echo "Media Server Stack"
	@echo ""
	@echo "Main commands:"
	@echo "  make setup      - Initial setup (auto-detect config)"
	@echo "  make start      - Start all services"
	@echo "  make stop       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs"
	@echo "  make status     - Check status"
	@echo "  make validate   - Validate configuration"
	@echo "  make clean      - Stop and remove containers"
	@echo ""
	@echo "Development:"
	@echo "  make format     - Format all files"

# Media Server Commands
setup:
	@./setup.sh

start:
	@./start.sh

stop:
	@docker compose down

restart:
	@docker compose restart

logs:
	@docker compose logs -f

status:
	@docker compose ps

validate:
	@./manage.py validate

clean:
	@docker compose down -v
	@echo "Containers and volumes removed (data preserved)"

# Formatting
format: format-python format-markdown format-docker
	@echo "✓ All files formatted!"

format-python:
	@echo "Formatting Python files with ruff..."
	@docker run --rm -v "$$(pwd):/work" -w /work \
		python:3.12-alpine \
		sh -c "pip install -q ruff && ruff format ."

format-markdown:
	@echo "Formatting Markdown files with prettier..."
	@docker run --rm -v "$$(pwd):/work" -w /work \
		node:20-alpine \
		sh -c "npx -y prettier@latest --write '**/*.md'"

format-docker:
	@echo "Formatting Dockerfiles with prettier..."
	@docker run --rm -v "$$(pwd):/work" -w /work \
		node:20-alpine \
		sh -c "npx -y prettier@latest --write '**/Dockerfile*' '**/*.dockerfile' || true"

.PHONY: help setup start stop restart logs status validate clean reset
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
	@echo "  make reset      - FULL RESET: Remove all configs (media preserved)"
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

reset:
	@echo "⚠️  WARNING: This will DELETE ALL service configurations!"
	@echo "   - All accounts, settings, and configs will be removed"
	@echo "   - Media files in $${DATA_ROOT}/media will be preserved"
	@echo "   - You will need to run 'make setup' again after this"
	@echo ""
	@read -p "Type 'DELETE' to confirm: " confirm && [ "$$confirm" = "DELETE" ] || (echo "Reset cancelled" && exit 1)
	@echo "Stopping containers..."
	@docker compose down
	@echo "Removing config directories..."
	@if [ -n "$${CONFIG_ROOT}" ] && [ -d "$${CONFIG_ROOT}" ]; then \
		rm -rf $${CONFIG_ROOT}/*/; \
		echo "✓ Configs removed from $${CONFIG_ROOT}"; \
	else \
		echo "No config directory found at $${CONFIG_ROOT}"; \
	fi
	@echo ""
	@echo "✓ Reset complete! Media preserved in $${DATA_ROOT}"
	@echo "Run 'make setup' to reconfigure services"

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

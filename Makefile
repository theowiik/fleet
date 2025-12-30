.PHONY: format format-python format-markdown format-docker format-nix help

help:
	@echo "Available targets:"
	@echo "  make format          - Format all files (Python, Markdown, Dockerfiles, Nix)"
	@echo "  make format-python   - Format Python files with ruff"
	@echo "  make format-markdown - Format Markdown files with prettier"
	@echo "  make format-docker   - Format Dockerfiles with prettier"

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

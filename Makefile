.PHONY: help install dev-install test lint format clean run example
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "🐝 Swarm Development Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

dev-install: ## Install development dependencies
	uv sync --dev

test: ## Run tests
	uv run pytest tests/ -v

lint: ## Run linting
	uv run ruff check swarm/
	uv run mypy swarm/

format: ## Format code
	uv run black swarm/ tests/ examples/
	uv run ruff check --fix swarm/

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf dist/
	rm -rf build/

run: ## Run Swarm CLI
	uv run swarm

example: ## Run basic example
	uv run python examples/basic_usage.py

install-browsers: ## Install Playwright browsers
	uv run playwright install

dev-setup: dev-install install-browsers ## Complete development setup
	@echo "✅ Development environment setup complete!"
	@echo "Try running: make example"

build: ## Build the package
	uv build

publish: ## Publish to PyPI (requires authentication)
	uv publish 
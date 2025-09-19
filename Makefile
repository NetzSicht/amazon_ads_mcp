.PHONY: help sync setup install dev-install run run-http test lint type-check verify docker-build docker-up docker-down docker-logs docker-ps clean clean-specs download-specs preprocess-specs process-specs check-specs diff-specs fix-single-spec minify-specs build-production run-production prettify-specs prepare-specs prepare-specs-quick full-setup

help:
	@echo "Available commands:"
	@echo "  make sync            Install dependencies via uv sync"
	@echo "  make setup           Install deps, lint (--fix), run tests"
	@echo "  make install         Install the package in editable mode"
	@echo "  make dev-install     Install with development dependencies"
	@echo "  make download-specs  Download all Amazon Ads OpenAPI specifications"
	@echo "  make preprocess-specs Optimize OpenAPI specs for MCP (requires ANTHROPIC_API_KEY)"
	@echo "  make prepare-specs   Complete pipeline to prepare specs for FastMCP (recommended)"
	@echo "  make process-specs   Process and fix OpenAPI specs with patches"
	@echo "  make check-specs     Check OpenAPI specs for issues (CI mode)"
	@echo "  make diff-specs      Show diffs for OpenAPI spec changes"
	@echo "  make fix-single-spec Fix a single spec (use SPEC=AccountsAdsAccounts)"
	@echo "  make minify-specs    Minify specs for production (saves ~20% space)"
	@echo "  make prettify-specs  Format specs for readability (development)"
	@echo "  make build-production Build production assets (process + minify)"
	@echo "  make run             Run the MCP server (development mode)"
	@echo "  make run-http        Run the MCP server with HTTP transport"
	@echo "  make run-production  Run server in production mode with minified specs"
	@echo "  make test            Run tests"
	@echo "  make lint            Run ruff linting with --fix"
	@echo "  make type-check      Run type checking"
	@echo "  make verify          Lint (--fix) then run the test suite"
	@echo "  make docker-build    Build Docker image (amazon-ads-mcp)"
	@echo "  make docker-up       Start docker-compose (server on port 9080)"
	@echo "  make docker-down     Stop docker-compose"
	@echo "  make docker-logs     Tail docker-compose logs"
	@echo "  make docker-ps       Show running containers for this project"
	@echo "  make clean           Clean up cache files"
	@echo "  make full-setup      Complete setup with all OpenAPI specs"

sync:
	uv sync

# Convenience alias matching the docs workflow
setup: sync lint test

install:
	uv pip install -e .

dev-install:
	uv pip install -e ".[dev]"

run:
	uv run python -m amazon_ads_mcp.server.mcp_server

run-http:
	uv run python -m amazon_ads_mcp.server.mcp_server --transport http --port 9080

download-specs:
	@echo "📥 Downloading Amazon Ads OpenAPI specifications..."
	uv pip install pyyaml
	uv run python scripts/download_openapi_specs.py
	@echo "🔄 Merging specifications..."
	uv run python scripts/merge_specs.py

preprocess-specs: download-specs
	@echo "🔧 Preprocessing OpenAPI specifications for MCP..."
	@if [ -f .env ]; then \
		export $$(grep -v '^#' .env | xargs); \
	fi; \
	if [ -z "$${ANTHROPIC_API_KEY}" ]; then \
		echo "❌ Error: ANTHROPIC_API_KEY not found in .env file"; \
		echo "  Add it to .env: ANTHROPIC_API_KEY=your-api-key"; \
		exit 1; \
	fi; \
	uv pip install anthropic && \
	uv run python scripts/preprocess_openapi.py openapi/amazon_ads_merged.json openapi/amazon_ads_merged_optimized.json
	@echo "✅ Preprocessing complete. Optimized spec saved to openapi/amazon_ads_merged_optimized.json"

test:
	uv run pytest

lint:
	uv run ruff check --fix

type-check:
	uv run mypy src/

verify: lint test

docker-build:
	docker build -t amazon-ads-mcp .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-ps:
	docker ps --filter "name=amazon-ads-mcp"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

clean-specs:
	rm -rf openapi/amazon_ads_apis
	rm -f openapi/amazon_ads_merged.json

# OpenAPI spec processing targets
process-specs: ## Process and fix OpenAPI specs with patches
	@echo "🔧 Processing OpenAPI specifications..."
	python .build/scripts/process_openapi_specs.py --fix
	@echo "✅ Specs processed successfully"

check-specs: ## Check OpenAPI specs for issues (CI mode)
	@echo "🔍 Checking OpenAPI specifications..."
	python .build/scripts/process_openapi_specs.py --check

diff-specs: ## Show diffs for OpenAPI spec changes
	python .build/scripts/process_openapi_specs.py --diff

fix-single-spec: ## Fix a single OpenAPI spec (use SPEC=AccountsAdsAccounts)
	@if [ -z "$(SPEC)" ]; then \
		echo "Usage: make fix-single-spec SPEC=AccountsAdsAccounts"; \
		exit 1; \
	fi
	python .build/scripts/process_openapi_specs.py --only $(SPEC) --fix --diff

minify-specs: ## Minify OpenAPI specs for production deployment
	@echo "📦 Minifying OpenAPI specifications..."
	python .build/scripts/minify_specs.py
	@echo "✅ Minified specs saved to dist/openapi/resources/"

build-production: ## Build production assets (process + minify specs)
	@echo "🚀 Building production assets..."
	python .build/scripts/build_production.py

run-production: build-production ## Run server with minified specs
	@echo "🚀 Starting server with optimized specs..."
	uv run python -m amazon_ads_mcp.server.mcp_server --transport http --port 9080

prettify-specs: ## Format OpenAPI specs for readability (development)
	@echo "🎨 Prettifying OpenAPI specifications..."
	@for file in openapi/resources/*.json; do \
		if [ -f "$$file" ]; then \
			python -m json.tool "$$file" > "$$file.tmp" && mv "$$file.tmp" "$$file"; \
			echo "  ✓ $$(basename $$file)"; \
		fi \
	done
	@echo "✅ All specs prettified"

prepare-specs:
	@echo "🚀 Running complete OpenAPI preparation pipeline for FastMCP..."
	uv run python scripts/prepare_openapi_for_fastmcp.py
	@echo "✅ Specs are ready for FastMCP!"
	@echo "   Final spec: openapi/amazon_ads_merged_optimized_resolved_clean_fixed.json"
	@echo "   Run 'make run' to start the MCP server"

prepare-specs-quick:
	@echo "🚀 Running OpenAPI preparation (skipping download)..."
	uv run python scripts/prepare_openapi_for_fastmcp.py --skip-download
	@echo "✅ Specs are ready for FastMCP!"

full-setup: install prepare-specs
	@echo "✅ Full setup complete with FastMCP-ready OpenAPI specifications"

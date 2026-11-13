.PHONY: up down logs migrate test lint format lock ingest eval

COMPOSE := docker compose
TOOLS := $(COMPOSE) run --rm --build tools

up: ## Build and start api, frontend and db
	$(COMPOSE) up --build -d

down: ## Stop the services
	$(COMPOSE) down

logs: ## Follow the service logs
	$(COMPOSE) logs -f

migrate: ## Apply pending database migrations (also done when `api` starts)
	$(COMPOSE) run --rm --build api alembic upgrade head

test: ## Unit and integration tests (starts `db` for the integration ones)
	$(TOOLS) pytest --cov=engine --cov-report=term-missing --cov-fail-under=90

lint: ## Ruff lint and format check
	$(TOOLS) ruff check .
	$(TOOLS) ruff format --check .

format: ## Apply ruff fixes and formatting
	$(TOOLS) ruff check --fix .
	$(TOOLS) ruff format .

lock: ## Regenerate uv.lock after changing pyproject.toml
	docker run --rm -v "$(CURDIR):/app" -w /app ghcr.io/astral-sh/uv:0.8-python3.12-bookworm-slim uv lock

ingest: ## Load the knowledge base (phase 4)
	@echo "make ingest: not implemented yet (phase 4)"

eval: ## RAG and guardrail evaluation (phase 4)
	@echo "make eval: not implemented yet (phase 4)"

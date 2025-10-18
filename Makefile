# Clean, minimal Makefile for common docker-compose dev tasks
COMPOSE := docker compose
APP := app
DB := db
APP_IMAGE ?= aequatio-app
# default DB URL (can be overridden by exporting DATABASE_URL env var)
DB_URL ?= postgresql+psycopg2://postgres:postgres@db:5432/aequatio
# Local DB URL for running app outside Docker
LOCAL_DB_URL ?= postgresql+psycopg2://postgres:postgres@localhost:5432/aequatio
# default compose network (project_default). Override if your project name differs.
NETWORK ?= aequatio_default

.PHONY: help up down build restart ps logs exec-app psql migrate migrate-run alembic-revision db-only migrate-local run-local local

help:
	@echo "Available targets:"
	@echo "  up                Build and start services in background"
	@echo "  down              Stop and remove containers"
	@echo "  build             Build service images"
	@echo "  restart           Recreate containers"
	@echo "  ps                Show compose services"
	@echo "  logs [service]    Follow logs (default: app)"
	@echo "  exec-app          Open a shell in the app container"
	@echo "  psql              Open psql shell in db container"
	@echo "  migrate           Run alembic upgrade head inside running app"
	@echo "  migrate-run       Run alembic upgrade head in a one-off container"
	@echo "  alembic-revision  Create a new alembic revision: make alembic-revision M='msg'"
	@echo "  dev               Start db, app and frontend, wait for db and run migrations"
	@echo "  db-only           Start only database in Docker"
	@echo "  migrate-local     Run migrations against local database (localhost:5432)"
	@echo "  run-local         Run FastAPI locally (requires db-only + migrate-local first)"
	@echo "  local             Complete local dev setup: start db, run migrations, start app locally"
	@echo "  lint             Run linter (ruff)"
	@echo "  lint-fix         Run linter and auto-fix issues (ruff --fix)"
	@echo "  format           Format code (black)"
	@echo "  typecheck       Run type checker (mypy)"
	@echo "  test             Run tests (pytest)"

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

restart: down up

ps:
	$(COMPOSE) ps


dev:
	@echo "Starting dev environment: db, app, frontend"
	$(COMPOSE) up -d --build db app frontend
	@echo "Waiting for Postgres to be ready..."
	@$(COMPOSE) exec -T db sh -c 'until pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB >/dev/null 2>&1; do sleep 1; done'
	@echo "Building application image for migrations"
	@docker build -t $(APP_IMAGE) .
	@echo "Running migrations in a temporary container (network: $(NETWORK))"
	@docker run --rm --network $(NETWORK) -e DATABASE_URL="$(DB_URL)" $(APP_IMAGE) uv run alembic upgrade head
	@echo "Dev environment ready"
	@echo "Frontend: http://127.0.0.1:5173"
	@echo "App:      http://127.0.0.1:8000"

db-only:
	@echo "Starting only the database in Docker..."
	$(COMPOSE) up -d db
	@echo "Waiting for Postgres to be ready..."
	@$(COMPOSE) exec -T db sh -c 'until pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB >/dev/null 2>&1; do sleep 1; done'
	@echo "Database is ready on localhost:5432"

migrate-local:
	@echo "Running migrations against local database..."
	@powershell -Command "$$env:DATABASE_URL='$(LOCAL_DB_URL)'; uv run alembic upgrade head"
	@echo "Migrations complete"

run-local:
	@echo "Starting FastAPI application locally..."
	@echo "Make sure you ran 'make db-only' and 'make migrate-local' first!"
	@powershell -Command "$$env:DATABASE_URL='$(LOCAL_DB_URL)'; uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

local: db-only migrate-local
	@echo ""
	@echo "=========================================="
	@echo "Local development environment ready!"
	@echo "=========================================="
	@echo "Database: postgres://localhost:5432/aequatio"
	@echo ""
	@echo "Now run: make run-local"
	@echo ""
	@echo "Or manually with PowerShell:"
	@echo "  $$env:DATABASE_URL='$(LOCAL_DB_URL)'; uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
	@echo "=========================================="
	@echo "=========================================="

logs:
	$(COMPOSE) logs -f $(or $(service),$(APP))

exec-app:
	$(COMPOSE) exec $(APP) /bin/bash

psql:
	$(COMPOSE) exec $(DB) psql -U postgres -d aequatio

migrate:
	$(COMPOSE) exec $(APP) uv run alembic upgrade head

migrate-run:
	$(COMPOSE) run --rm $(APP) uv run alembic upgrade head

alembic-revision:
	@test -n "$(M)" || (echo "Missing message: make alembic-revision M=\"your message\"" && exit 1)
	$(COMPOSE) exec $(APP) uv run alembic revision --autogenerate -m "$(M)"

lint:
	uv tool run ruff check .

lint-fix:
	uv tool run ruff check . --fix

format:
	uv tool run black .

test:
	uv tool run pytest -q

typecheck:
	uv tool run mypy .

check: lint typecheck test
	@echo "All checks finished"
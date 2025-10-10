# Makefile for common developer commands
# Note: On Windows you need GNU make (e.g., via Chocolatey) or use the commands directly in PowerShell.

SHELL := /bin/bash

.PHONY: help lint lint-fix format test typecheck check docker-build docker-up docker-down docker-logs docker-setup

help:
	@echo "Available targets:"
	@echo "  lint        - run ruff"
	@echo "  lint-fix    - run ruff --fix"
	@echo "  format      - run black"
	@echo "  test        - run pytest"
	@echo "  typecheck   - run mypy"
	@echo "  check       - lint + typecheck + test"
	@echo "  docker-setup - build and start docker-compose services"
	@echo "  docker-build - build docker-compose images"
	@echo "  docker-up    - start docker-compose services (detached)"
	@echo "  docker-down  - stop and remove docker-compose services"
	@echo "  docker-logs  - follow docker-compose logs"

lint:
	uv tool run ruff check

lint-fix:
	uv tool run ruff check --fix

format:
	uv tool run black .

test:
	uv tool run pytest -q

typecheck:
	uv tool run mypy .

check: lint typecheck test
	@echo "All checks finished"

docker-build:
	docker compose build --pull

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down --volumes --remove-orphans

docker-logs:
	docker compose logs -f

docker-setup: docker-build docker-up
	@echo "Docker environment built and started (use 'make docker-logs' to follow logs)"

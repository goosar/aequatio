# Makefile for common developer commands
# Note: On Windows you need GNU make (e.g., via Chocolatey) or use the commands directly in PowerShell.

.PHONY: help lint lint-fix format test typecheck check

HELP_TEXT = \
"Available targets:\n\tmake lint       - run ruff (lint)\n\tmake lint-fix   - run ruff --fix to apply auto-fixes\n\tmake format     - run black to format code\n\tmake test       - run pytest\n\tmake typecheck  - run mypy type checks\n\tmake check      - run lint, typecheck and tests\n"

help:
	@echo $(HELP_TEXT)

lint:
	@uv tool run ruff check

lint-fix:
	@uv tool run ruff check --fix

format:
	@uv tool run black .

test:
	@uv tool run pytest -q

typecheck:
	@uv tool run mypy .

check: lint typecheck test

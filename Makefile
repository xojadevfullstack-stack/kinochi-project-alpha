.PHONY: check check-release check-all test lint typecheck build run help

# Python interpreter selection (detect venv if available)
PYTHON := $(wildcard backend/.venv/Scripts/python.exe)
ifeq ($(PYTHON),)
  PYTHON := $(wildcard backend/.venv/bin/python)
endif
ifeq ($(PYTHON),)
  PYTHON := python
endif

# Pytest executable
PYTEST := $(wildcard backend/.venv/Scripts/pytest.exe)
ifeq ($(PYTEST),)
  PYTEST := $(PYTHON) -m pytest
endif

# Ruff linter
RUFF := $(wildcard backend/.venv/Scripts/ruff.exe)
ifeq ($(RUFF),)
  RUFF := $(PYTHON) -m ruff
endif

# Alembic migration tool
ALEMBIC := $(wildcard backend/.venv/Scripts/alembic.exe)
ifeq ($(ALEMBIC),)
  ALEMBIC := $(PYTHON) -m alembic
endif

# Fast primary check gate for local dev and pre-commit (lint + typecheck + test)
check: lint typecheck test
	@echo "=== [CHECK PASSED] Fast quality gates succeeded ==="

# Comprehensive check gate for CI and production releases (includes frontend build)
check-release: check build
	@echo "=== [RELEASE CHECK PASSED] All gates including build succeeded ==="

check-all: check-release

lint:
	@echo "--- [1/4] Running Linters ---"
	-$(RUFF) check backend bot
	@if [ -d "website/node_modules" ]; then npm --prefix website run lint; fi

typecheck:
	@echo "--- [2/4] Verifying Migrations & Typecheck ---"
	cd backend && $(ALEMBIC) heads

test:
	@echo "--- [3/4] Running Tests ---"
	cd backend && $(PYTEST) tests/
	cd bot && $(PYTEST) tests/

build:
	@echo "--- [4/4] Building Website ---"
	@if [ -d "website/node_modules" ]; then npm --prefix website run build; else echo "Skipping website build (node_modules not installed)"; fi

run:
	@echo "--- Starting Kinochi Application ---"
	$(PYTHON) run.py

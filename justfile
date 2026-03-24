# Default recipe - show available commands
default:
    @just --list

# Run linter
lint:
    uv run ruff check .

# Run formatter check
format-check:
    uv run ruff format --check .

# Format code
format:
    uv run ruff format .

# Fix auto-fixable lint issues
fix:
    uv run ruff check --fix .
    uv run ruff format .

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info

# Build package
build: clean
    uv build

# Install git hooks
hooks:
    uv run pre-commit install

# Run type checker
typecheck:
    uv run ty check karat/

# Run unit tests
test-unit *args:
    uv run pytest {{args}}

# Run tests with coverage (fails if under threshold)
test-cov:
    uv run pytest --cov --cov-report=term-missing

# Run tests with coverage for CI (outputs XML, excludes e2e which needs a real PTY)
test-ci:
    uv run pytest --cov --cov-report=xml --ignore=tests/e2e

# Run integration tests
test-integration:
    uv run pytest tests/integration/

# Watch unit tests
test-unit-watch *args:
    uv run ptw --now karat karat/ {{args}}

# Watch integration tests
test-integration-watch *args:
    uv run ptw --now tests/integration tests/integration/ {{args}}

# Run local CI checks. Lint/format/typecheck in parallel, then unit tests.
ci:
    #!/usr/bin/env bash
    set -euo pipefail
    just lint &
    just format-check &
    just typecheck &
    wait
    just test-unit

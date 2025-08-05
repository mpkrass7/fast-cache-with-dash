.PHONY: install install-dev run run-demo clean lint format check typecheck test test-cov install-playwright test-e2e test-e2e-ui test-e2e-debug test-e2e-headed test-e2e-report test-e2e-all

# Install production dependencies using uv
install:
	uv pip install -r src/requirements.txt

# Install development dependencies using uv
install-dev:
	uv pip install -r src/requirements.txt
	uv pip install ruff isort mypy

# Run the main application (connects to Databricks)
run:
	uv run python src/app.py

# Lint code with ruff
lint:
	uv run ruff format .
	uv run ruff check . --fix
	uv run isort .

# Run type checking with mypy
typecheck:
	mypy . --ignore-missing-imports

# Clean up any temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".ruff_cache" -delete
	find . -type d -name ".mypy_cache" -delete

# Run tests with pytest
test:
	uv run python -m pytest src/tests/ -v

# Run tests with coverage
test-cov:
	uv run python -m pytest src/tests/ -v --cov=. --cov-report=html --cov-report=term

# Playwright E2E Testing
install-playwright:
	uv pip install playwright pytest-playwright requests
	uv run playwright install

test-e2e:
	uv run python -m pytest src/tests/e2e/ -v

test-e2e-ui:
	uv run python -m pytest src/tests/e2e/ -v --headed

test-e2e-debug:
	uv run python -m pytest src/tests/e2e/ -v --headed --pdb

test-e2e-headed:
	uv run python -m pytest src/tests/e2e/ -v --headed

test-e2e-report:
	uv run python -m pytest src/tests/e2e/ -v --html=playwright-report/report.html
	open playwright-report/report.html

test-e2e-all: install-playwright test-e2e

# Help
help:
	@echo "Available commands:"
	@echo "  install     - Install production dependencies using uv"
	@echo "  install-dev - Install development dependencies using uv"
	@echo "  run         - Run main app (connects to Databricks)"
	@echo "  run-demo    - Run demo app (uses sample data)"
	@echo "  lint        - Lint code with ruff"
	@echo "  format      - Format code with ruff and isort"
	@echo "  typecheck   - Run type checking with mypy"
	@echo "  check       - Run linting and formatting checks"
	@echo "  test        - Run tests with pytest"
	@echo "  test-cov    - Run tests with coverage"
	@echo "  clean       - Clean up temporary files"
	@echo "  install-playwright - Install Playwright and dependencies"
	@echo "  test-e2e    - Run E2E tests with Playwright"
	@echo "  test-e2e-ui - Run E2E tests with UI mode"
	@echo "  test-e2e-debug - Run E2E tests in debug mode"
	@echo "  test-e2e-headed - Run E2E tests with headed browser"
	@echo "  test-e2e-report - Run E2E tests and open HTML report"
	@echo "  test-e2e-all - Install Playwright and run all E2E tests"
	@echo "  help        - Show this help message" 
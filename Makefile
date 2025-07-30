.PHONY: install install-dev run run-demo clean lint format check typecheck test test-cov

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
	ruff format .
	ruff check . --fix
	isort .


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
	@echo "  help        - Show this help message" 
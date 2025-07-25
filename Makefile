.PHONY: install install-dev run run-demo clean lint format check typecheck

# Install production dependencies using uv
install:
	uv pip install -r requirements.txt

# Install development dependencies using uv
install-dev:
	uv pip install -r requirements.txt
	uv pip install ruff isort mypy

# Run the main application (connects to Databricks)
run:
	python app.py

# Run the demo application (uses sample data)
run-demo:
	python demo_app.py

# Lint code with ruff
lint:
	ruff format .
	ruff check . --fix
	isort .

# Format code with ruff and isort
format:
	ruff format .
	isort .

# Run type checking with mypy
typecheck:
	mypy . --ignore-missing-imports

# Run all code quality checks (linting and formatting only)
check: lint format

# Clean up any temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".ruff_cache" -delete
	find . -type d -name ".mypy_cache" -delete

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
	@echo "  clean       - Clean up temporary files"
	@echo "  help        - Show this help message" 
# Tests

This directory contains unit tests for the `db_helpers` module.

## Structure

- `conftest.py` - Shared pytest fixtures and configuration
- `test_db_helpers.py` - Unit tests for the QueryCache class and related functionality

## Running Tests

### Run all tests:
```bash
make test
```

### Run specific test file:
```bash
python -m pytest tests/test_db_helpers.py -v
```

### Run specific test class:
```bash
python -m pytest tests/test_db_helpers.py::TestQueryCache -v
```

### Run specific test method:
```bash
python -m pytest tests/test_db_helpers.py::TestQueryCache::test_query_cache_initialization -v
```

## Test Coverage

The tests cover QueryCache releated stuff since the purpose of this project is to implement an in-memory cache. They don't cover anything on the frontend.

## Fixtures

Shared fixtures are defined in `conftest.py`:

- `mock_db_config` - Mock database configuration
- `sample_filters` - Sample filter dictionary for testing
- `sample_dataframe` - Sample DataFrame for testing

## Dependencies

Tests require:
- pytest
- pandas
- duckdb
- unittest.mock (built-in)

Install test dependencies:
```bash
uv pip install pytest pytest-cov
``` 
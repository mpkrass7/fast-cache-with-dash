"""
Shared pytest configuration and fixtures for the test suite.
"""

from unittest.mock import Mock

import pandas as pd
import pytest


@pytest.fixture(scope="session")
def mock_db_config():
    """Mock database configuration for all tests"""
    config = Mock()
    config.host = "test-host"
    config.authenticate = "test-auth"
    return config


@pytest.fixture
def sample_filters():
    """Sample filters for testing"""
    return {
        "paymentMethod": "amex",
        "product": ["Golden Gate Ginger", "Tokyo Tidbits"],
        "country": "USA",
    }


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing"""
    return pd.DataFrame(
        {
            "dateTime": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "product": ["Golden Gate Ginger", "Tokyo Tidbits", "Pearly Pies"],
            "quantity": [1, 2, 3],
            "unitPrice": [10.99, 15.50, 12.75],
            "totalPrice": [10.99, 31.00, 38.25],
            "paymentMethod": ["amex", "visa", "mastercard"],
            "city": ["San Francisco", "Tokyo", "New York"],
            "country": ["USA", "Japan", "USA"],
            "size": ["M", "L", "S"],
        }
    )

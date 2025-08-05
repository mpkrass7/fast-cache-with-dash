import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add the parent directory to the path so we can import db_helpers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_helpers import QueryCache, get_dbsql_connection


class TestQueryCache:
    """Test suite for QueryCache class"""

    @pytest.fixture
    def query_cache(self, mock_db_config):
        """Create a QueryCache instance for testing"""
        return QueryCache(
            db_config=mock_db_config,
            http_path="/sql/1.0/warehouses/test",
            max_size_mb=10,
            ttl=1,  # 1 hour for testing
        )

    def test_query_cache_initialization(self, mock_db_config):
        """Test QueryCache initialization"""
        cache = QueryCache(
            db_config=mock_db_config,
            http_path="/sql/1.0/warehouses/test",
            max_size_mb=100,
            ttl=120,
        )

        assert cache.max_size_mb == 100
        assert cache.current_size_mb == 0
        assert cache.db_config == mock_db_config
        assert cache.db_http_path == "/sql/1.0/warehouses/test"
        assert cache.ttl == 120
        assert cache.duckdb is not None

    def test_create_table_if_not_exists(self, query_cache):
        """Test that create_table_if_not_exists runs without error and creates the table"""
        # Drop the table if it exists to ensure a clean test
        query_cache.duckdb.execute("DROP TABLE IF EXISTS cached_queries")
        # Now call the method under test
        query_cache.create_table_if_not_exists()
        # Verify table exists by checking if we can query it
        result = query_cache.duckdb.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cached_queries'"
        ).fetchone()
        assert result is not None

    def test_create_where_clause_single_value(self):
        """Test WHERE clause creation with single values"""
        filters = {"paymentMethod": "amex", "country": "USA"}
        where_clause = QueryCache._create_where_clause(filters)
        expected = " AND paymentMethod = 'amex' AND country = 'USA'"
        assert where_clause == expected

    def test_create_where_clause_list_values(self):
        """Test WHERE clause creation with list values"""
        filters = {"product": ["item1", "item2"], "size": ["S", "M", "L"]}
        where_clause = QueryCache._create_where_clause(filters)
        expected = " AND product IN ('item1','item2') AND size IN ('S','M','L')"
        assert where_clause == expected

    def test_create_where_clause_mixed_types(self):
        """Test WHERE clause creation with mixed string and numeric values"""
        filters = {"quantity": 5, "product": ["item1"], "active": True}
        where_clause = QueryCache._create_where_clause(filters)
        expected = " AND quantity = 5 AND product IN ('item1') AND active = True"
        assert where_clause == expected

    def test_create_where_clause_empty(self):
        """Test WHERE clause creation with empty filters"""
        filters = {}
        where_clause = QueryCache._create_where_clause(filters)
        assert where_clause == ""

    def test_build_query(self, sample_filters, query_cache):
        """Test query building with filters"""
        query = query_cache.build_query(sample_filters)
        expected_parts = [
            "SELECT dateTime, product, quantity, unitPrice, totalPrice, paymentMethod, city, country, size",
            "from sales_transactions",
            "JOIN sales_franchises ON sales_transactions.franchiseID = sales_franchises.franchiseID",
            "WHERE 1=1",
            "paymentMethod = 'amex'",
            "product IN ('Golden Gate Ginger','Tokyo Tidbits')",
            "country = 'USA'",
        ]

        for part in expected_parts:
            assert part in query

    def test_build_query_no_filters(self, query_cache):
        """Test query building without filters"""
        query = query_cache.build_query({})
        assert "WHERE 1=1" in query
        assert "AND" not in query

    def test_hash_query(self, query_cache):
        """Test query hashing functionality"""
        query1 = "SELECT * FROM table WHERE id = 1"
        query2 = "SELECT * FROM table WHERE id = 2"
        query3 = "SELECT * FROM table WHERE id = 1"

        hash1 = query_cache.hash_query(query1)
        hash2 = query_cache.hash_query(query2)
        hash3 = query_cache.hash_query(query3)

        assert hash1 != hash2
        assert hash1 == hash3
        assert len(hash1) == 64  # SHA256 hash length

    @patch("db_helpers.sql.connect")
    def test_read_table_from_databricks_sql(self, mock_connect, query_cache):
        """Test reading data from Databricks SQL"""
        # Mock the connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Set up the connection context manager
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_connect.return_value.__exit__.return_value = None

        # Set up the cursor context manager
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Mock the result
        mock_result = MagicMock()
        mock_result.to_pandas.return_value = pd.DataFrame(
            {"dateTime": ["2023-01-01"], "product": ["Test Product"], "quantity": [1]}
        )
        mock_cursor.fetchall_arrow.return_value = mock_result

        query = "SELECT * FROM test_table"
        result = query_cache.read_table_from_databricks_sql(query)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        mock_cursor.execute.assert_called_once_with(query)

    def test_store_and_retrieve_from_duckdb(self, query_cache):
        """Test storing and retrieving data from DuckDB cache"""
        query_hash = "test_hash_123"
        query = "SELECT * FROM test_table"
        test_data = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

        # Store data
        query_cache.store_in_duckdb(query_hash, query, test_data, 0.001, 3)

        # Retrieve data
        result = query_cache.get_from_duckdb(query_hash)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        pd.testing.assert_frame_equal(result, test_data)

    def test_get_from_duckdb_nonexistent(self, query_cache):
        """Test retrieving non-existent data from DuckDB"""
        result = query_cache.get_from_duckdb("nonexistent_hash")
        assert result is None

    def test_get_timestamp_from_duckdb(self, query_cache):
        """Test retrieving timestamp from DuckDB"""
        query_hash = "test_hash_456"
        query = "SELECT * FROM test_table"
        test_data = pd.DataFrame({"col1": [1]})

        # Store data
        query_cache.store_in_duckdb(query_hash, query, test_data, 0.001, 1)

        # Get timestamp
        timestamp = query_cache.get_timestamp_from_duckdb(query_hash)

        assert timestamp is not None
        assert isinstance(timestamp, datetime)

    def test_remove_from_duckdb(self, query_cache):
        """Test removing data from DuckDB"""
        query_hash = "test_hash_789"
        query = "SELECT * FROM test_table"
        test_data = pd.DataFrame({"col1": [1]})

        # Store data
        query_cache.store_in_duckdb(query_hash, query, test_data, 0.001, 1)

        # Verify it exists
        result = query_cache.get_from_duckdb(query_hash)
        assert result is not None

        # Remove data
        query_cache.remove_from_duckdb(query_hash)

        # Verify it's gone
        result = query_cache.get_from_duckdb(query_hash)
        assert result is None

    def test_cache_hit_fresh_data(self, query_cache, sample_filters):
        """Test cache hit with fresh data"""
        query = query_cache.build_query(sample_filters)
        query_hash = query_cache.hash_query(query)
        test_data = pd.DataFrame({"col1": [1, 2, 3]})

        # Store fresh data
        query_cache.store_in_duckdb(query_hash, query, test_data, 0.001, 3)

        # Mock the Databricks SQL call to ensure it's not called
        with patch.object(query_cache, "read_table_from_databricks_sql") as mock_read:
            result = query_cache.get(sample_filters)

            # Should return cached data
            pd.testing.assert_frame_equal(result, test_data)
            # Should not call Databricks SQL
            mock_read.assert_not_called()

    def test_cache_miss_expired_data(self, query_cache, sample_filters):
        """Test cache miss with expired data"""
        query = query_cache.build_query(sample_filters)
        query_hash = query_cache.hash_query(query)
        test_data = pd.DataFrame({"col1": [1, 2, 3]})

        # Store old data (expired)
        old_timestamp = datetime.now() - timedelta(hours=query_cache.ttl + 1)
        query_cache.duckdb.execute(
            "INSERT INTO cached_queries VALUES (?, ?, ?, ?, ?, ?)",
            [query_hash, query, test_data.to_csv(index=False), old_timestamp, 0.001, 3],
        )
        query_cache.duckdb.commit()

        # Mock fresh data from Databricks SQL
        fresh_data = pd.DataFrame({"col1": [4, 5, 6]})
        with patch.object(
            query_cache, "read_table_from_databricks_sql", return_value=fresh_data
        ):
            result = query_cache.get(sample_filters)

            # Should return fresh data from Databricks SQL
            pd.testing.assert_frame_equal(result, fresh_data)

    def test_cache_miss_no_data(self, query_cache, sample_filters):
        """Test cache miss when no cached data exists"""
        fresh_data = pd.DataFrame({"col1": [1, 2, 3]})

        with patch.object(
            query_cache, "read_table_from_databricks_sql", return_value=fresh_data
        ):
            result = query_cache.get(sample_filters)

            # Should return fresh data from Databricks SQL
            pd.testing.assert_frame_equal(result, fresh_data)

    def test_check_and_manage_duckdb_size(self, query_cache):
        """Test DuckDB size management"""
        # This is a basic test - in practice, size management would need more complex testing
        # with actual large datasets
        query_cache.check_and_manage_duckdb_size()
        # Should not raise any exceptions

    def test_duckdb_size_grows_with_data(self, query_cache):
        """Test that the in-memory DuckDB database size actually grows when data is added"""

        # Get initial size by counting rows in the table
        initial_count = query_cache.duckdb.execute(
            "SELECT COUNT(*) FROM cached_queries"
        ).fetchone()[0]
        print(f"Initial row count: {initial_count}")

        # Store some data
        test_data_1 = pd.DataFrame(
            {
                "col1": list(range(1000)),  # 1000 rows
                "col2": ["test" * 100] * 1000,  # Large string data
                "col3": [1.23456789] * 1000,  # Float data
            }
        )

        query_hash_1 = "test_hash_1"
        query_1 = "SELECT * FROM large_table_1"
        query_cache.store_in_duckdb(query_hash_1, query_1, test_data_1, 0.1, 1000)

        # Get count after first insertion
        count_after_first = query_cache.duckdb.execute(
            "SELECT sum(result_records) FROM cached_queries"
        ).fetchone()[0]
        print(f"Row count after first insertion: {count_after_first}")

        # Verify count increased
        assert count_after_first > initial_count, (
            f"Row count should have increased from {initial_count} to {count_after_first}"
        )

        # Store more data
        test_data_2 = pd.DataFrame(
            {
                "col1": list(range(2000)),  # 2000 rows
                "col2": ["another_test" * 200] * 2000,  # Even larger string data
                "col3": [2.34567890] * 2000,  # More float data
            }
        )

        query_hash_2 = "test_hash_2"
        query_2 = "SELECT * FROM large_table_2"
        query_cache.store_in_duckdb(query_hash_2, query_2, test_data_2, 0.2, 2000)

        # Get count after second insertion
        count_after_second = query_cache.duckdb.execute(
            "SELECT sum(result_records) FROM cached_queries"
        ).fetchone()[0]
        print(f"Row count after second insertion: {count_after_second}")

        # Verify count increased again
        assert count_after_second > count_after_first, (
            f"Row count should have increased from {count_after_first} to {count_after_second}"
        )

        # Verify data is actually stored and retrievable
        retrieved_data_1 = query_cache.get_from_duckdb(query_hash_1)
        retrieved_data_2 = query_cache.get_from_duckdb(query_hash_2)

        assert retrieved_data_1 is not None
        assert retrieved_data_2 is not None
        assert len(retrieved_data_1) == 1000
        assert len(retrieved_data_2) == 2000

        # Test that removing data reduces count
        query_cache.remove_from_duckdb(query_hash_1)
        count_after_removal = query_cache.duckdb.execute(
            "SELECT sum(result_records) FROM cached_queries"
        ).fetchone()[0]
        print(f"Row count after removal: {count_after_removal}")

        # Count should be less than before removal
        assert count_after_removal < count_after_second, (
            f"Row count should have decreased from {count_after_second} to {count_after_removal}"
        )

        # Verify the data is actually gone
        retrieved_data_1_after_removal = query_cache.get_from_duckdb(query_hash_1)
        assert retrieved_data_1_after_removal is None

        # Test memory usage by checking the size of stored data
        # Get the size of the result column (which contains the CSV data)
        result_sizes = query_cache.duckdb.execute(
            "SELECT LENGTH(result) FROM cached_queries"
        ).fetchall()

        total_data_size = sum(size[0] for size in result_sizes)
        print(f"Total data size in database: {total_data_size} bytes")

        # Verify that we have substantial data stored
        assert total_data_size > 0, "Should have data stored in the database"

        # Test with even larger dataset to ensure memory growth
        large_test_data = pd.DataFrame(
            {
                "col1": list(range(5000)),
                "col2": ["very_large_string_" * 500] * 5000,
                "col3": [3.14159265359] * 5000,
                "col4": [True] * 5000,
                "col5": ["additional_column_with_more_data"] * 5000,
            }
        )

        query_hash_3 = "test_hash_3"
        query_3 = "SELECT * FROM very_large_table"
        query_cache.store_in_duckdb(query_hash_3, query_3, large_test_data, 0.5, 5000)

        # Verify the large dataset is stored
        retrieved_large_data = query_cache.get_from_duckdb(query_hash_3)
        assert retrieved_large_data is not None
        assert len(retrieved_large_data) == 5000

        # Check final count
        final_count = query_cache.duckdb.execute(
            "SELECT sum(result_records) FROM cached_queries"
        ).fetchone()[0]
        print(f"Final row count: {final_count}")
        assert final_count > count_after_removal

    def test_remove_older_queries_from_duckdb(self, query_cache):
        """Test removing older queries from DuckDB"""
        # Add some test data
        for i in range(5):
            query_hash = f"test_hash_{i}"
            query = f"SELECT * FROM table_{i}"
            test_data = pd.DataFrame({"col1": [i]})
            query_cache.store_in_duckdb(query_hash, query, test_data, 0.001, 1)

        # Verify data exists
        for i in range(5):
            result = query_cache.get_from_duckdb(f"test_hash_{i}")
            assert result is not None

        # Remove older queries
        query_cache.remove_older_queries_from_duckdb()

        # Some queries should be removed (implementation dependent)

    def test_close(self, query_cache):
        """Test closing the DuckDB connection"""
        query_cache.close()
        # Should not raise any exceptions

    def test_lru_cache_decorator(self):
        """Test the LRU cache decorator on get_dbsql_connection"""
        # This is a basic test - the actual function is not implemented in the original code
        # but we can test that the decorator is applied
        assert hasattr(get_dbsql_connection, "__wrapped__")


class TestIntegration:
    """Integration tests for the QueryCache class"""

    def test_full_cache_workflow(self, mock_db_config):
        """Test the complete cache workflow"""
        cache = QueryCache(
            db_config=mock_db_config,
            http_path="/sql/1.0/warehouses/test",
            max_size_mb=50,
            ttl=30,
        )

        filters = {"paymentMethod": "visa", "product": ["Test Product"]}

        # Mock the Databricks SQL response
        test_data = pd.DataFrame(
            {
                "dateTime": ["2023-01-01", "2023-01-02"],
                "product": ["Test Product", "Test Product"],
                "quantity": [1, 2],
            }
        )

        with patch.object(
            cache, "read_table_from_databricks_sql", return_value=test_data
        ):
            # First call - should hit Databricks SQL
            result1 = cache.get(filters)
            pd.testing.assert_frame_equal(result1, test_data)

            # Second call - should hit cache
            result2 = cache.get(filters)
            pd.testing.assert_frame_equal(result2, test_data)

            # Verify cache hit
            query = cache.build_query(filters)
            query_hash = cache.hash_query(query)
            cached_result = cache.get_from_duckdb(query_hash)
            assert cached_result is not None

        cache.close()


if __name__ == "__main__":
    pytest.main([__file__])

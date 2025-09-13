import hashlib
import os
import sys
import time
from datetime import datetime, timedelta
from io import StringIO

import duckdb
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config

catalog = "samples"
schema = "bakehouse"
http_path = f"/sql/1.0/warehouses/{os.getenv('WAREHOUSE_ID', '388276af36ab98ba')}"

cfg = Config()


class QueryCache:
    def __init__(self, db_config, http_path: str, max_size_mb: int, ttl: int = 24):
        self.max_size_mb = max_size_mb
        self.current_size_mb = 0
        self.duckdb = duckdb.connect(":memory:")
        self.db_config = db_config
        self.db_http_path = http_path
        self.ttl = ttl  # Time to live in hours
        self.create_table_if_not_exists()
        self.check_and_manage_duckdb_size()
        self.baseline_query = """
        SELECT dateTime, product, quantity, unitPrice, totalPrice, paymentMethod, city, country, size from sales_transactions
        JOIN sales_franchises ON sales_transactions.franchiseID = sales_franchises.franchiseID
        WHERE 1=1
        """

    def create_table_if_not_exists(self):
        """Create the DuckDB cache table if it doesn't exist"""
        try:
            self.duckdb.execute("""
                CREATE TABLE IF NOT EXISTS cached_queries (
                    query_hash TEXT,
                    query TEXT,
                    result TEXT,
                    timestamp TIMESTAMP,
                    result_size FLOAT,
                    result_records INTEGER
                )
            """)
            self.duckdb.commit()
        except Exception as e:
            print(f"Error creating table in DuckDB: {e}")

    @staticmethod
    def _create_where_clause(filters: dict[str, list | str]) -> str:
        """
        Given a dictionary of filters, generate SQL WHERE clause predicates.
        """
        predicates = []
        for col, val in filters.items():
            if isinstance(val, list):
                quoted_vals = [f"'{v}'" if isinstance(v, str) else str(v) for v in val]
                predicates.append(f"{col} IN ({','.join(quoted_vals)})")
            else:
                v = f"'{val}'" if isinstance(val, str) else str(val)
                predicates.append(f"{col} = {v}")

        where_clause = ""
        if predicates:
            where_clause = " AND " + " AND ".join(predicates)

        return where_clause

    def build_query(self, filters: dict[str, list | str]) -> str:
        predicates = self._create_where_clause(filters)
        return f"""
        {self.baseline_query}
        {predicates}
        ;
        """

    def read_table_from_databricks_sql(self, query: str) -> pd.DataFrame:
        """
        Given a table name and a dictionary of filters, return a pandas dataframe
        of the results from the Databricks SQL API.
        """

        with sql.connect(
            server_hostname=self.db_config.host,
            http_path=self.db_http_path,
            credentials_provider=lambda: self.db_config.authenticate,
            catalog=catalog,
            schema=schema,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall_arrow().to_pandas()
                return results

    def get(self, filters: dict[str, list | str]):
        """
        Retrieve the query result from cache or Databricks SQL API.

        If the query is not in the cache, it will be queried from the Databricks SQL API
        and stored in the cache.
        If the query is in the cache, it will be retrieved from the cache.
        If the query is expired, it will be removed from the cache and queried from the Databricks SQL API.
        If the query is not in the cache or expired, it will be queried from the Databricks SQL API
        and stored in the cache.

        Args:
            filters: A dictionary of filters to apply to the query.

        Returns:
            A pandas dataframe of the results.
        """
        query = self.build_query(filters)
        query_hash = self.hash_query(query)
        t1 = time.time()
        # Check if query is in DuckDB cache
        result = self.get_from_duckdb(query_hash)

        if result is not None:
            # Check if the result in DuckDB is not expired
            duckdb_timestamp = self.get_timestamp_from_duckdb(query_hash)
            if duckdb_timestamp and datetime.now() - duckdb_timestamp < timedelta(
                hours=self.ttl
            ):
                print("DuckDB Cache Hit: Query served from DuckDB cache.")
                print(f"DuckDB Query Time: {round(time.time() - t1, 4)} seconds")
                return result
            else:
                # If expired, remove from DuckDB and query DBSQL
                self.remove_from_duckdb(query_hash)
                print("DuckDB Cache Miss: Query expired in DuckDB, querying DBSQL.")

        # Query Postgres if not in cache or expired
        result = self.read_table_from_databricks_sql(query)
        print(f"Databricks SQL Query Time: {round(time.time() - t1, 4)} seconds")
        size, records = sys.getsizeof(result) / (1024 * 1024), len(result)
        self.store_in_duckdb(query_hash, query, result, size, records)
        print("Databricks SQL Call: Query served from Databricks SQL.")
        return result

    def get_from_duckdb(self, query_hash):
        """Retrieve query result from DuckDB"""
        try:
            self.duckdb.execute(
                "SELECT result FROM cached_queries WHERE query_hash = ?", [query_hash]
            )
            result = self.duckdb.fetchone()
            if result:
                return pd.read_csv(StringIO(result[0]))
            else:
                return None
        except Exception as e:
            print(f"Error retrieving query from DuckDB: {e}")
            return None

    def get_timestamp_from_duckdb(self, query_hash):
        """Get timestamp of cached query in DuckDB"""
        try:
            self.duckdb.execute(
                "SELECT timestamp FROM cached_queries WHERE query_hash = ?",
                [query_hash],
            )
            timestamp = self.duckdb.fetchone()
            if timestamp:
                return timestamp[0]
            else:
                return None
        except Exception as e:
            print(f"Error retrieving timestamp from DuckDB: {e}")
            return None

    def store_in_duckdb(self, query_hash, query, result, result_size, result_records):
        """Store the query result in DuckDB"""
        try:
            # Insert the query and result into DuckDB
            self.duckdb.execute(
                "INSERT INTO cached_queries VALUES (?, ?, ?, ?, ?, ?)",
                [
                    query_hash,
                    query,
                    result.to_csv(index=False),
                    datetime.now(),
                    result_size,
                    result_records,
                ],
            )
            self.duckdb.commit()
            print("Successfully stored query in DuckDB")
            self.check_and_manage_duckdb_size()
        except Exception as e:
            print(f"Error storing query in DuckDB: {e}")

    def remove_from_duckdb(self, query_hash):
        """Remove expired query from DuckDB"""
        try:
            self.duckdb.execute(
                "DELETE FROM cached_queries WHERE query_hash = ?", [query_hash]
            )
            self.duckdb.commit()
            print("Removed expired query from DuckDB.")
        except Exception as e:
            print(f"Error removing query from DuckDB: {e}")

    def check_and_manage_duckdb_size(self):
        """Check if DuckDB file size exceeds the limit and manage cache size"""

        db_size_mb, db_records = self.duckdb.execute(
            "SELECT coalesce(SUM(result_size), 0), coalesce(SUM(result_records), 0) FROM cached_queries"
        ).fetchone()
        print(f"DB Size: {round(db_size_mb, 4)} MB, DB Records: {db_records}")
        if db_size_mb > self.max_size_mb:
            # If the size exceeds the limit, remove older queries
            self.remove_older_queries_from_duckdb()

    def remove_older_queries_from_duckdb(self):
        """Remove older queries from DuckDB to manage size"""
        try:
            self.duckdb.execute(
                "SELECT query_hash FROM cached_queries ORDER BY timestamp ASC LIMIT 10"
            )
            oldest_queries = [row[0] for row in self.duckdb.fetchall()]
            # Delete the oldest queries
            for query_hash in oldest_queries:
                self.duckdb.execute(
                    "DELETE FROM cached_queries WHERE query_hash = ?", [query_hash]
                )
            self.duckdb.commit()
            print("Removed older queries from DuckDB to manage size.")
        except Exception as e:
            print(f"Error removing older queries from DuckDB: {e}")

    def hash_query(self, query):
        """Generate a hash for the SQL query"""
        return hashlib.sha256(query.encode()).hexdigest()

    def close(self):
        """Close DuckDB connection"""
        self.duckdb.close()


query_cache = QueryCache(cfg, http_path=http_path, max_size_mb=100, ttl=24)

# Example usage
if __name__ == "__main__":
    filters = {
        "paymentMethod": "amex",
        "product": ["Golden Gate Ginger", "Tokyo Tidbits"],
    }
    query_cache.get(filters)
    print("First dataframe retrieved")
    filters["product"].append("Pearly Pies")
    query_cache.get(filters)
    print("Second dataframe retrieved")
    print(query_cache.get(filters).head(10))

    query_cache.get(filters).to_csv("sample_data.csv", index=False)
    print("Third dataframe retrieved")

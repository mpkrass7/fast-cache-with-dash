import hashlib
import json
import os
import time

import duckdb
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config

cfg = Config()  # Set the DATABRICKS_HOST environment variable when running locally
catalog = "samples"
schema = "bakehouse"
http_path = f"/sql/1.0/warehouses/{os.getenv('WAREHOUSE_ID', '072b588d901e6eed')}"
in_memory_db = duckdb.connect(":memory:")


def get_connection():
    """
    Given an http path, return a connection to the Databricks SQL API.
    """
    return sql.connect(
        server_hostname=cfg.host,
        http_path=http_path,
        credentials_provider=lambda: cfg.authenticate,
        catalog=catalog,
        schema=schema,
    )


def _read_table_from_databricks_sql(
    filters: dict[str, list | str], conn
) -> pd.DataFrame:
    """
    Given a table name and a dictionary of filters, return a pandas dataframe
    of the results.
    """
    predicates = _create_where_clause(filters)

    with conn.cursor() as cursor:
        query = f"""
        SELECT dateTime, product, quantity, unitPrice, totalPrice, paymentMethod, city, country, size from sales_transactions
JOIN sales_franchises ON sales_transactions.franchiseID = sales_franchises.franchiseID
        WHERE 1=1
        {predicates}
        ;
        """
        cursor.execute(query)
        results = cursor.fetchall_arrow().to_pandas()
        time.sleep(3)  # To help make it more obvious that the query is running
        return results


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


def _create_filter_hash(filters: dict[str, list | str]) -> str:
    """
    Given a dictionary of filters, create a hash string representing the filter selection.
    """
    s = json.dumps(filters, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:8]


def get_dataframe(conn, filters: dict[str, list | str]) -> pd.DataFrame:
    """
    Given a table name and a dictionary of filters, return a pandas dataframe
    of the results.
    """
    hash_value = f"query_{_create_filter_hash(filters)}"

    try:
        next(
            table[0]
            for table in in_memory_db.execute("SHOW TABLES").fetchall()
            if table[0] == hash_value
        )
        return in_memory_db.execute(f"SELECT * FROM {hash_value}").df()
    except StopIteration:
        df = _read_table_from_databricks_sql(filters, conn)
        in_memory_db.register(hash_value, df)
        return df


if __name__ == "__main__":
    filters = {
        "paymentMethod": "amex",
        "product": ["Golden Gate Ginger", "Tokyo Tidbits"],
    }
    conn = get_connection()
    get_dataframe(conn, filters)
    print("First dataframe retrieved")
    filters["product"].append("Pearly Pies")
    get_dataframe(conn, filters)
    print("Second dataframe retrieved")
    print(get_dataframe(conn, filters).head(10))
    get_dataframe(conn, filters).to_csv("sample_data.csv")
    print("Third dataframe retrieved")
    conn.close()

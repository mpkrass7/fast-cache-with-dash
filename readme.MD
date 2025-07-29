# Fast Cache with Dash and DuckDB 📊

Memoization is a technique used to speed up computer programs by storing the results of expensive function calls and returning the cached result when the same inputs occur again.

This is a basic Dash web application that demonstrates **in-memory caching** of Databricks SQL queries on the **bakehouse schema** using DuckDB. 

## 🚀 Quick Start

Make sure you have a virtual environment with uv installed.

1. **Install dependencies:**
```bash
make install
```

2. **Set up Databricks credentials:**
```bash
export DATABRICKS_HOST="your-databricks-workspace-url"
export DATABRICKS_WAREHOUSE_ID="your-warehouse-id"
```

3. **Run the app:**
```bash
python app.py
```

4. **Open dashboard:** http://localhost:8050

## 🎯 What It Does

- **Interactive filters** for payment method, product, and country
- **Real-time queries** to Databricks SQL (bakehouse schema)
- **Smart caching** using DuckDB in-memory storage with hash-based cache keys

## 🏗️ Architecture

- **Dash** for the web interface
- **DuckDB** for in-memory caching
- **Databricks SQL** for data source
- **Plotly** for visualizations

## 🛠️ Development

```bash
make install-dev  # Install dev tools
make lint         # Run linting
make format       # Format code
```

## 📁 Files

- `app.py` - Main Dash application
- `db_helpers.py` - Databricks connection & caching
- `visualizations.py` - Chart & table components


Credit:
    - Soumil Shah's implementation of a Postgres Query Cache with DuckDB: https://github.com/soumilshah1995/PostgresQueryCache-DuckDB/tree/main
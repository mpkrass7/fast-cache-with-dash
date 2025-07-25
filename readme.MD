# Sales Data Dashboard 📊

A modern Dash dashboard that demonstrates **in-memory caching** with Databricks SQL using the **bakehouse schema**. 

## 🚀 Quick Start

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

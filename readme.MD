# Sales Data Dashboard

A modern, interactive dashboard built with Dash that connects to Databricks SQL and provides real-time data visualization with intelligent caching.

## Features

- **Interactive Filters**: Multi-select dropdowns for payment method, product, and country
- **Real-time Data**: Connects to Databricks SQL with intelligent caching using DuckDB
- **Beautiful Visualizations**: Multiple chart types including bar charts, pie charts, histograms, and time series
- **Summary Cards**: Key metrics displayed in an attractive card layout
- **Data Table**: Paginated table with formatted data display
- **Responsive Design**: Modern UI with clean styling

## Installation

1. Install the required dependencies using uv:
```bash
make install
# or
uv pip install -r requirements.txt
```

2. For development (includes linting tools):
```bash
make install-dev
# or
uv pip install -r requirements.txt
uv pip install ruff black isort mypy
```

2. Set up your Databricks environment variables:
```bash
export DATABRICKS_HOST="your-databricks-workspace-url"
export DATABRICKS_WAREHOUSE_ID="your-warehouse-id"
```

## Usage

### Main Application (Connects to Databricks)

Run the main application that connects to your Databricks SQL warehouse:

```bash
python app.py
```

The dashboard will be available at `http://localhost:8050`

### Demo Application (Uses Sample Data)

For testing or demonstration purposes, run the demo version that uses the sample CSV data:

```bash
python demo_app.py
```

The demo dashboard will be available at `http://localhost:8051`

## How to Use the Dashboard

1. **Select Filters**: Use the dropdown menus to filter by:
   - Payment Method (visa, amex, mastercard)
   - Product (various bakery items)
   - Country (multiple countries)

2. **Query Data**: Click the "Query Data" button to fetch data from Databricks (or filter sample data in demo mode)

3. **View Results**: The dashboard will display:
   - **Summary Cards**: Total sales, transactions, average transaction, and unique products
   - **Charts**: 
     - Sales by Product (horizontal bar chart)
     - Sales by Country (horizontal bar chart)
     - Payment Method Distribution (pie chart)
     - Quantity Distribution (histogram)
     - Daily Sales Timeline (line chart)
   - **Data Table**: Paginated table with all filtered data

## Caching System

The application uses an intelligent caching system:

- **DuckDB In-Memory Cache**: Queries are cached in memory using DuckDB
- **Hash-Based Caching**: Each unique filter combination gets a unique cache key
- **Automatic Cache Management**: Results are automatically cached and retrieved for identical queries

## File Structure

```
dash-cache/
├── app.py              # Main Dash application (connects to Databricks)
├── demo_app.py         # Demo version (uses sample data)
├── helpers.py          # Data fetching and caching logic
├── requirements.txt    # Python dependencies
├── sample_data.csv     # Sample data for testing
├── README.md          # This file
└── Makefile           # Build and run commands
```

## Data Schema

The dashboard expects data with the following columns:
- `dateTime`: Transaction timestamp
- `product`: Product name
- `quantity`: Quantity sold
- `unitPrice`: Price per unit
- `totalPrice`: Total transaction amount
- `paymentMethod`: Payment method used
- `city`: City where transaction occurred
- `country`: Country where transaction occurred
- `size`: Product size

## Customization

### Adding New Filters

To add new filter options, modify the `filter_options` dictionary in `app.py`:

```python
filter_options = {
    "paymentMethod": ["visa", "amex", "mastercard"],
    "product": ["Product1", "Product2", ...],
    "country": ["Country1", "Country2", ...],
    "newFilter": ["option1", "option2", ...]  # Add new filter here
}
```

### Adding New Charts

To add new visualizations, create new callback functions and add them to the layout:

```python
@app.callback(
    Output('new-chart', 'figure'),
    [Input('data-store', 'data')]
)
def update_new_chart(data):
    # Your chart logic here
    pass
```

## Troubleshooting

### Common Issues

1. **Connection Errors**: Ensure your Databricks environment variables are set correctly
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **Port Conflicts**: Change the port in the app.run_server() call if 8050/8051 are in use

### Demo Mode

If you don't have access to Databricks, use the demo application:
```bash
python demo_app.py
```

This will use the sample data provided in `sample_data.csv` and allow you to test all dashboard features.

## Development

### Code Quality

The project includes comprehensive linting and formatting tools:

```bash
# Lint code with ruff
make lint

# Format code with black and isort
make format

# Run all code quality checks
make check
```

### Running in Development Mode

Both applications run in debug mode by default, which provides:
- Hot reloading of changes
- Detailed error messages
- Debug toolbar

### Making Changes

1. Modify the layout in the `app.layout` section
2. Add new callbacks for interactivity
3. Update the styling in the `style` dictionaries
4. Run `make check` to ensure code quality
5. Test changes by refreshing the browser

## License

This project is open source and available under the MIT License.
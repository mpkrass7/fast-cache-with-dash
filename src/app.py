import dash
from dash import Input, Output, State, dcc, html

from db_helpers import query_cache
from visualizations import make_charts, make_data_table, make_summary_cards

# Initialize the Dash app
app = dash.Dash(__name__, title="Sales Data Dashboard")


# Filter options
filter_options = {
    "paymentMethod": ["visa", "amex", "mastercard"],
    "product": [
        "Austin Almond Biscotti",
        "Golden Gate Ginger",
        "Orchard Oasis",
        "Outback Oatmeal",
        "Pearly Pies",
        "Tokyo Tidbits",
    ],
    "country": [
        "Australia",
        "Sweden",
        "Canada",
        "Italy",
        "Netherlands",
        "US",
        "Japan",
        "Germany",
        "France",
    ],
}

# App layout
app.layout = html.Div(
    [
        # Header
        html.H1(
            "Sales Data Dashboard",
            style={"textAlign": "center", "marginBottom": "30px"},
        ),
        # Filters Section
        html.Div(
            [
                html.H3("Filters", style={"marginBottom": "20px"}),
                # Filter dropdowns in a grid
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(
                                    "Payment Method:", style={"fontWeight": "bold"}
                                ),
                                dcc.Dropdown(
                                    id="payment-method-dropdown",
                                    options=[
                                        {"label": method.title(), "value": method}
                                        for method in filter_options["paymentMethod"]
                                    ],
                                    placeholder="Select payment method...",
                                    multi=True,
                                ),
                            ],
                            style={
                                "width": "30%",
                                "display": "inline-block",
                                "marginRight": "20px",
                            },
                        ),
                        html.Div(
                            [
                                html.Label("Product:", style={"fontWeight": "bold"}),
                                dcc.Dropdown(
                                    id="product-dropdown",
                                    options=[
                                        {"label": product, "value": product}
                                        for product in filter_options["product"]
                                    ],
                                    placeholder="Select products...",
                                    multi=True,
                                ),
                            ],
                            style={
                                "width": "30%",
                                "display": "inline-block",
                                "marginRight": "20px",
                            },
                        ),
                        html.Div(
                            [
                                html.Label("Country:", style={"fontWeight": "bold"}),
                                dcc.Dropdown(
                                    id="country-dropdown",
                                    options=[
                                        {"label": country, "value": country}
                                        for country in filter_options["country"]
                                    ],
                                    placeholder="Select countries...",
                                    multi=True,
                                ),
                            ],
                            style={"width": "30%", "display": "inline-block"},
                        ),
                    ],
                    style={"marginBottom": "20px"},
                ),
                # Query Button
                html.Button(
                    "Query Data",
                    id="query-button",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#3498db",
                        "color": "white",
                        "padding": "12px 24px",
                        "border": "none",
                        "borderRadius": "5px",
                        "fontSize": "16px",
                        "cursor": "pointer",
                    },
                ),
            ],
            style={
                "backgroundColor": "#f8f9fa",
                "padding": "20px",
                "borderRadius": "10px",
                "marginBottom": "30px",
            },
        ),
        # Results Section
        dcc.Loading(
            id="loading-query-button",
            type="circle",
            # Set to top of div
            style={
                "position": "absolute",
                "top": "0",
                "left": "0",
                "right": "0",
                "bottom": "0",
            },
            overlay_style={"visibility": "visible", "filter": "blur(2px)"},
            children=html.Div(
                [
                    # Summary cards
                    html.Div(id="summary-cards", style={"marginBottom": "30px"}),
                    # Charts Section
                    html.Div(
                        [
                            html.H4("Charts", style={"marginBottom": "20px"}),
                            # First row of charts
                            html.Div(
                                [
                                    html.Div(
                                        [dcc.Graph(id="sales-by-product-chart")],
                                        style={
                                            "width": "50%",
                                            "display": "inline-block",
                                        },
                                    ),
                                    html.Div(
                                        [dcc.Graph(id="sales-by-country-chart")],
                                        style={
                                            "width": "50%",
                                            "display": "inline-block",
                                        },
                                    ),
                                ],
                                style={"marginBottom": "30px"},
                            ),
                            # Second row of charts
                            html.Div(
                                [
                                    html.Div(
                                        [dcc.Graph(id="payment-method-chart")],
                                        style={
                                            "width": "50%",
                                            "display": "inline-block",
                                        },
                                    ),
                                    html.Div(
                                        [dcc.Graph(id="quantity-distribution-chart")],
                                        style={
                                            "width": "50%",
                                            "display": "inline-block",
                                        },
                                    ),
                                ],
                                style={"marginBottom": "30px"},
                            ),
                            # Third row - time series
                            html.Div(
                                [dcc.Graph(id="sales-timeline-chart")],
                                style={"marginBottom": "30px"},
                            ),
                        ],
                        id="charts-section",
                        style={"display": "none"},
                    ),
                    # Data Table Section
                    html.Div(
                        [
                            html.H4("Data Table", style={"marginBottom": "20px"}),
                            html.Div(id="data-table-container"),
                        ],
                        id="table-section",
                        style={"display": "none"},
                    ),
                ],
                id="results-section",
                style={"display": "none"},
            ),
        ),
        # Store for the data
        dcc.Store(id="data-store"),
    ],
    style={"padding": "20px"},
)


# Callback to handle data query
@app.callback(
    [
        Output("data-store", "data"),
        Output("results-section", "style"),
    ],
    [Input("query-button", "n_clicks")],
    [
        State("payment-method-dropdown", "value"),
        State("product-dropdown", "value"),
        State("country-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def query_data(n_clicks, payment_method, product, country):
    if n_clicks == 0:
        return None, {"display": "none"}
    try:
        # Build filters dictionary
        filters = {}
        if payment_method:
            filters["paymentMethod"] = (
                payment_method if isinstance(payment_method, list) else [payment_method]
            )
        if product:
            filters["product"] = product if isinstance(product, list) else [product]
        if country:
            filters["country"] = country if isinstance(country, list) else [country]

        df = query_cache.get(filters)

        # Convert to JSON for storage
        data = df.to_dict("records")

        return data, {"display": "block"}

    except Exception as _:
        # Return empty data and hide results on error
        return None, {"display": "none"}


# Callback to update summary cards
@app.callback(Output("summary-cards", "children"), [Input("data-store", "data")])
def update_summary_cards(data):
    return make_summary_cards(data)


# Callback to update charts
@app.callback(
    [
        Output("charts-section", "style"),
        Output("sales-by-product-chart", "figure"),
        Output("sales-by-country-chart", "figure"),
        Output("payment-method-chart", "figure"),
        Output("quantity-distribution-chart", "figure"),
        Output("sales-timeline-chart", "figure"),
    ],
    [Input("data-store", "data")],
)
def update_charts(data):
    return make_charts(data)


# Callback to update data table
@app.callback(
    [Output("table-section", "style"), Output("data-table-container", "children")],
    [Input("data-store", "data")],
)
def update_data_table(data):
    return make_data_table(data)


# Run the app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)

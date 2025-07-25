import pandas as pd
import plotly.express as px
from dash import dash_table, html


def make_summary_cards(
    data: pd.DataFrame,
) -> tuple[html.Div, html.Div, html.Div, html.Div]:
    if not data:
        return []
    df = pd.DataFrame(data)

    # Calculate summary statistics
    total_sales = df["totalPrice"].sum()
    total_transactions = len(df)
    avg_transaction = df["totalPrice"].mean()
    unique_products = df["product"].nunique()

    cards = [
        html.Div(
            [
                html.H4(
                    f"${total_sales:,.2f}", style={"color": "#27ae60", "margin": "0"}
                ),
                html.P("Total Sales", style={"margin": "0", "fontSize": "14px"}),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "textAlign": "center",
                "width": "23%",
                "display": "inline-block",
                "marginRight": "2%",
            },
        ),
        html.Div(
            [
                html.H4(
                    f"{total_transactions:,}", style={"color": "#3498db", "margin": "0"}
                ),
                html.P("Total Transactions", style={"margin": "0", "fontSize": "14px"}),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "textAlign": "center",
                "width": "23%",
                "display": "inline-block",
                "marginRight": "2%",
            },
        ),
        html.Div(
            [
                html.H4(
                    f"${avg_transaction:.2f}", style={"color": "#f39c12", "margin": "0"}
                ),
                html.P("Avg Transaction", style={"margin": "0", "fontSize": "14px"}),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "textAlign": "center",
                "width": "23%",
                "display": "inline-block",
                "marginRight": "2%",
            },
        ),
        html.Div(
            [
                html.H4(
                    f"{unique_products}", style={"color": "#9b59b6", "margin": "0"}
                ),
                html.P("Unique Products", style={"margin": "0", "fontSize": "14px"}),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "textAlign": "center",
                "width": "23%",
                "display": "inline-block",
            },
        ),
    ]
    return cards


def make_charts(
    data: pd.DataFrame,
) -> tuple[px.bar, px.bar, px.pie, px.histogram, px.line]:
    if not data:
        return {"display": "none"}, {}, {}, {}, {}, {}

    df = pd.DataFrame(data)

    df["dateTime"] = pd.to_datetime(df["dateTime"])

    # 1. Sales by Product
    product_sales = (
        df.groupby("product")["totalPrice"].sum().sort_values(ascending=True)
    )
    product_chart = px.bar(
        x=product_sales.values,
        y=product_sales.index,
        orientation="h",
        title="Total Sales by Product",
        labels={"x": "Total Sales ($)", "y": "Product"},
        color=product_sales.values,
        color_continuous_scale="Blues",
    )
    product_chart.update_layout(height=400, showlegend=False)

    # 2. Sales by Country
    country_sales = (
        df.groupby("country")["totalPrice"].sum().sort_values(ascending=True)
    )
    country_chart = px.bar(
        x=country_sales.values,
        y=country_sales.index,
        orientation="h",
        title="Total Sales by Country",
        labels={"x": "Total Sales ($)", "y": "Country"},
        color=country_sales.values,
        color_continuous_scale="Greens",
    )
    country_chart.update_layout(height=400, showlegend=False)

    # 3. Payment Method Distribution
    payment_counts = df["paymentMethod"].value_counts()
    payment_chart = px.pie(
        values=payment_counts.values,
        names=payment_counts.index,
        title="Transactions by Payment Method",
    )
    payment_chart.update_layout(height=400)

    # 4. Quantity Distribution
    quantity_chart = px.histogram(
        df,
        x="quantity",
        nbins=20,
        title="Distribution of Quantities",
        labels={"quantity": "Quantity", "count": "Number of Transactions"},
    )
    quantity_chart.update_layout(height=400)

    # 5. Sales Timeline
    if "dateTime" in df.columns:
        df["date"] = df["dateTime"].dt.date
        daily_sales = df.groupby("date")["totalPrice"].sum().reset_index()
        timeline_chart = px.line(
            daily_sales,
            x="date",
            y="totalPrice",
            title="Daily Sales Timeline",
            labels={"date": "Date", "totalPrice": "Total Sales ($)"},
        )
        timeline_chart.update_layout(height=400)
    else:
        timeline_chart = px.line(title="Daily Sales Timeline (No date data available)")
        timeline_chart.update_layout(height=400)

    return (
        {"display": "block"},
        product_chart,
        country_chart,
        payment_chart,
        quantity_chart,
        timeline_chart,
    )


def make_data_table(data: pd.DataFrame) -> tuple[html.Div, html.Div]:
    if not data:
        return {"display": "none"}, []

    df = pd.DataFrame(data)

    # Format the dataframe for display
    display_df = df.copy()

    display_df["dateTime"] = pd.to_datetime(display_df["dateTime"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    display_df["totalPrice"] = display_df["totalPrice"].apply(lambda x: f"${x:.2f}")
    display_df["unitPrice"] = display_df["unitPrice"].apply(lambda x: f"${x:.2f}")

    table = dash_table.DataTable(
        data=display_df.to_dict("records"),
        columns=[{"name": i, "id": i} for i in display_df.columns],
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "10px",
            "minWidth": "100px",
            "maxWidth": "200px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_header={
            "backgroundColor": "#f8f9fa",
            "fontWeight": "bold",
            "border": "1px solid #dee2e6",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"}
        ],
    )

    return {"display": "block"}, table

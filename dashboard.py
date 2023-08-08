import dash
from data_loader.get_data import GetStockData
from data_loader.misc_connect import MongoConnect
from gui.screen_1.callbacks import register_analytics_callbacks
from gui.screen_2.callbacks import register_trade_callbacks
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from gui.screen_1.layout import get_analytics_layout
from gui.screen_2.layout import get_trading_layout  # New layout for trading simulation
# Add other necessary imports

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Function to create dropdown
data_fetcher = GetStockData()
tickers = data_fetcher.get_ticker_names()
tickers = frozenset(tickers)
names = [ticker + ":" + (data_fetcher.get_ticker_field_info(ticker, field='longName') or ticker) for ticker in tickers]

m = MongoConnect()
hamburger = html.Div(
    [
        html.Div(className="bar1", style = {"padding-left": "3%"}),
        html.Div(className="bar2", style = {"padding-left": "3%"}),
        html.Div(className="bar3", style = {"padding-left": "3%"}),
    ],
    id="hamburger",
    style={"cursor": "pointer", "padding-top": "0%"},
)

sidebar = html.Div(
    [
        dbc.Nav(
            [
                dbc.NavLink("Financial Analysis Dashboard", href="/", id="analytics-link", style={"align": "middle"}),
                dbc.NavLink("Trading Simulation", href="/trading", id="trading-link"),
            ],
            style={"margin-left": "3%", "opacity": 0, "padding-top": "3%"},
            id="sidebar-links",
            className="sidebar-closed"
        ),
    ],
    id="sidebar",
    className="sidebar-closed",
    style={"padding-top": "3%"}
)


# Define the content area

# Define the content area
content = html.Div(id="page-content", style={"margin-left": "5%", "margin-right": "5%", "align":"center"})
loading_state = dcc.Store(id='loading-state', data={'loaded': False})
app.layout = html.Div([dcc.Location(id="url"), hamburger, sidebar, content], style={'width': '100%', 'max-width': 'none'})


# Define callback to update page content based on URL
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/trading':
        layout = get_trading_layout(names)
        return layout

    else:
        layout = get_analytics_layout(names)
        return layout


# Register other necessary callbacks
@app.callback(
    [Output("sidebar", "className"), Output("hamburger", "className"), Output("sidebar-links", "style")],
    [Input("hamburger", "n_clicks")],
    [State("sidebar", "className"), State("hamburger", "className")],
)
def toggle_sidebar(n_clicks, sidebar_class, hamburger_class):
    if n_clicks and n_clicks % 2 != 0:
        return "sidebar-open", "change", {"opacity": 1, "margin-left": "3%"}
    else:
        return "sidebar-closed", "", {"opacity": 0, "margin-left": "3%"}

register_analytics_callbacks(app, data_fetcher, m)
register_trade_callbacks(app, data_fetcher, m)


if __name__ == "__main__":
    app.run_server(debug=True)

# DASH IMPORTS
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
from data_loader.singleton import get_data_fetcher

# GUI INTERFACE
from gui.screen_1.callbacks import register_analytics_callbacks
from gui.screen_2.callbacks import register_trade_callbacks
from gui.screen_1.layout import get_analytics_layout
from gui.screen_2.layout import get_trading_layout  

data_fetcher = get_data_fetcher()

# LOADERS
def run_dashboard():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True, prevent_initial_callbacks="initial_duplicate")
    
    # Function to create dropdown
    
    
    tickers = data_fetcher.get_ticker_names()
    tickers = frozenset(tickers)
    names = [ticker + ":" + (data_fetcher.get_ticker_field_info(ticker, field='longName') or ticker) for ticker in tickers]
    
    hamburger = dbc.Button(
        [
            html.Div(className="bar1"),
            html.Div(className="bar2"),
            html.Div(className="bar3"),
        ],
        id="hamburger",
        style={"cursor": "pointer", "position": "fixed", "top": "15px", "left": "15px", "z-index": "1000", "background": "none", "border": "none"},
        n_clicks=0,
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
    
    
    content = html.Div(id="page-content", style={"margin-left": "5%", "margin-right": "5%", "align":"center"})
    loading_state = dcc.Store(id='loading-state', data={'loaded': False})
    outside_click_detector = html.Div(id="outside-click-detector", style={"position": "fixed", "width": "100%", "height": "100%", "z-index": "0"})
    
    app.layout = html.Div([dcc.Location(id="url"), outside_click_detector, hamburger, sidebar, content], style={'width': '100%', 'max-width': 'none'})
    
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
    
    @app.callback(
        [Output("sidebar", "className"), Output("hamburger", "className"), Output("sidebar-links", "style"), Output("outside-click-detector", "style")],
        [Input("hamburger", "n_clicks"), Input("outside-click-detector", "n_clicks")],
        [State("sidebar", "className")],
    )
    def toggle_sidebar(hamburger_clicks, outside_clicks, sidebar_class):
        ctx = dash.callback_context
        if not ctx.triggered:
            return "sidebar-closed", "", {"opacity": 0, "margin-left": "3%"}, {"z-index": "0"}
    
        if sidebar_class == "sidebar-closed":
            return "sidebar-open", "change", {"opacity": 1, "margin-left": "3%"}, {"z-index": "999"}
        else:
            return "sidebar-closed", "", {"opacity": 0, "margin-left": "3%"}, {"z-index": "0"}
        
    
    register_analytics_callbacks(app)
    register_trade_callbacks(app, names)
    
    app.run_server(debug=True)
    
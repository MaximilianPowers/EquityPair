from dash import dcc, html
import dash_bootstrap_components as dbc

from datetime import datetime

from gui.utils import create_slider, create_dropdown, create_divider

def get_trading_layout(names):
    layout = html.Div([
        dbc.Container([
            get_title(),
            run_single_trade(names),
            create_divider(),
            load_trade(),
            evaluate_trade(),
            create_divider(),
        ], style={'width': '90%', 'max-width': 'none', 'margin-bottom': '200px'}),
    ])
    return layout
def get_title():
    return dbc.Row(dbc.Col(html.H1("Trading Simulation")), style={'margin-bottom': '20px', 'padding-top': "8%"})

def run_single_trade(names):
    title = dbc.Row(dbc.Col(html.H2("Run Single Pair Strategies")), style={'margin-bottom': '20px'})
    
    input_ = dbc.Row([
        dbc.Col(create_dropdown('trade-ticker-dropdown-1', names, ["CDMO", "GOLF"]), width=3),
        dbc.Col(dcc.Dropdown(
                id = 'choose-method-dropdown',
                options = [
                    {'label': 'Kalman', 'value': 'Kalman', 'search': 'Kalman Regression'},
                    {'label': 'OLS', 'value': 'OLS', 'search': 'OLS Regression'},
                ],
                value = 'OLS',
                multi=False
        ), width=3),
        dbc.Col(dcc.DatePickerRange(
        id='train-date-1',
        min_date_allowed=datetime(2013, 1, 1),
        max_date_allowed=datetime.today(),
        initial_visible_month=datetime.today(),
        start_date=datetime(2020, 6, 1),
        end_date=datetime(2022, 6, 1),
    ), width="auto"),
        dbc.Col(dcc.DatePickerRange(
        id='trade-date-1',
        min_date_allowed=datetime(2013, 1, 1),
        max_date_allowed=datetime.today(),
        initial_visible_month=datetime.today(),
        start_date=datetime(2022, 6, 2),
        end_date=datetime(2023, 7, 1),
    ), width="auto"),
    ],  style={'margin-bottom': '20px'})
    hyperparameters = dbc.Row([
        create_slider('slider-sigma-buy', 0, 5, 0.1, 1),
        create_slider('slider-sigma-sell-low', 0, 2, 0.1, 0.2),
        create_slider('slider-sigma-sell-high', 2, 10, 0.1, 4),
        create_slider('slider-maxlen', 10, 5000, 50, 1000),
        create_slider('slider-adf-window', 10, 3000, 50, 600),
        dbc.Col(dbc.Button(
            "Submit", id="run-trade-button", color="primary"
            ),
            width="auto",
            style={'overflow': 'visible', 'text-align': 'left'}
        )
    ], style={'margin-bottom': '10px'})


    # Main trading graph placeholder
    #trading_graph = dbc.Row([
    #    dbc.Col([
    #        dcc.Graph(id='trading-graph', figure={'data': []})  # Empty graph
    #    ], width=12),
    #], style={'margin-bottom': '20px'})

    res = dbc.Row([
        dbc.Col([
                dcc.Graph(id='trade-results-1')
            ], width=8),
            dbc.Col([
                dcc.Graph(id='trade-results-2')
            ], width=4)
    ], style={'margin-bottom': '10px'})

    res_2 = dbc.Row([
        dbc.Col([
                dcc.Graph(id='trade-results-3')
            ], width=8),
            dbc.Col([
                dcc.Graph(id='trade-results-4')
            ], width=4)
    ], style={'margin-bottom': '30px'})

    return html.Div([title, input_, hyperparameters, res, res_2])

def load_trade():
    title = dbc.Row(dbc.Col(html.H2("Post-Trade Analysis")), style={'margin-bottom': '20px'})

    layout = dbc.Row([
                    dcc.Store(id='uuid-storage-1'),
                    dcc.Store(id='uuid-storage-2'),
                    dcc.Store(id='uuid-storage-3'),
                    dcc.Store(id='uuid-storage-4'),
                    dcc.Store(id='uuid-storage-final'),
                      
                    dbc.Col([
                        dcc.Dropdown(
                            id='search-option',
                            options=[
                                {'label': 'Specific Strategy', 'value': 'specific'},
                                {'label': 'Aggregate Most Profitable', 'value': 'profitable'},
                                {'label': 'Aggregate by Tickers', 'value': 'tickers'},
                                {'label': 'Aggregate by Method', 'value': 'method'},
                                {'label': 'Search by UUID', 'value': 'uuid'}
                            ],
                            placeholder='Select a search option',
                        ),
                    ], width=2),
                    dbc.Col(id='search-parameters', width=9),  # Adjust width as needed
                ])
    empty_div = html.Div(id='empty-div', style={'display': 'none'})
    return html.Div([title, layout, empty_div], style={'margin-bottom': '20px'})


def evaluate_trade():
    input_ = dbc.Row([
        create_slider('risk-free-rate', 0, 0.1, 0.01, 0.01),
        create_slider('target-return', 0, 0.15, 0.01, 0.01),
        dbc.Col(dbc.Button("Evaluate", id="evaluate-button", color="primary"), width="auto", style={'overflow': 'visible', 'text-align': 'left'}),
    ], style={'margin-bottom': '10px', 'margin-top': '40px'})

       # Subfigures
    risk_metric_subfigures_1 = dbc.Row([
        dbc.Col([dcc.Graph(id='risk-metric-graph-1')], width=6),
        dbc.Col([dcc.Graph(id='risk-metric-graph-2')], width=6),
    ], style={'margin-bottom': '10px'})

    risk_metric_subfigures_2 = dbc.Row([
        dbc.Col([dcc.Graph(id='risk-metric-graph-3')], width=6),
        dbc.Col([dcc.Graph(id='risk-metric-graph-4')], width=6),
    ], style={'margin-bottom': '10px'})

    # Combine subfigures and table
    risk_metric_graphs = dbc.Row([
        dbc.Col([risk_metric_subfigures_1, risk_metric_subfigures_2], width=6), # Subfigures
        dbc.Col([
                html.Div(id='strategy-data-1')
            ], width=6), # Table
    ], style={'margin-bottom': '10px'})

    # Overall portfolio values graph placeholder

    return html.Div([input_, risk_metric_graphs])

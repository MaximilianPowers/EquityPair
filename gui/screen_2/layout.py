from dash import dcc, html
import dash_bootstrap_components as dbc
from gui.utils import create_slider, create_dropdown, create_date_picker
from datetime import datetime

def get_trading_layout(names):
    layout = html.Div([
        dbc.Container([
            get_title(),
            run_single_trade(names),
        ], style={'width': '90%', 'max-width': 'none'}),
    ])
    return layout
def get_title():
    return dbc.Row(dbc.Col(html.H1("Trading Simulation")), style={'margin-bottom': '20px', 'padding-top': "8%"})

def run_single_trade(names):
    title = dbc.Row(dbc.Col(html.H2("Run Single Pair Strategies")), style={'margin-bottom': '20px'})
    
    input_ = dbc.Row([
        dbc.Col(create_dropdown('trade-ticker-dropdown-1', names, ['MD', 'EA']), width=3),
        dbc.Col(dcc.Dropdown(
                id = 'choose-method-dropdown',
                options = [
                    {'label': 'Kalman', 'value': 'Kalman', 'search': 'Kalman Regression'},
                    {'label': 'OLS', 'value': 'OLS', 'search': 'OLS Regression'},
                ],
                value = 'Kalman',
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
        create_slider('slider-sigma-sell-low', 0, 10, 0.1, 0.2),
        create_slider('slider-sigma-sell-high', 0, 3, 0.05, 2),
        create_slider('slider-maxlen', 0, 5000, 1, 1000),
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
    ], style={'margin-bottom': '20px'})

    return html.Div([title, input_, hyperparameters, res, res_2])

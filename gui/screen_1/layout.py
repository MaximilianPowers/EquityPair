from dash import dcc, html
import dash_bootstrap_components as dbc
from gui.utils import create_dropdown, create_date_picker, create_button_with_loading, create_slider

# Define the layout here
def get_analytics_layout(names):
    layout = html.Div([
        dbc.Container([
            get_title(),
            identify_stat_and_mr(names),
            cluster_tickers(),
            pair_identification(),
            hedging_ratio(names)
        ], style={'width': '90%', 'max-width': 'none'}),
    ])
    return layout


def get_title():
    return dbc.Row(dbc.Col(html.H1("Financial Analysis Dashboard")), style={'margin-bottom': '20px', 'padding-top': "8%"})

def identify_stat_and_mr(names):
    title = dbc.Row(dbc.Col(html.H2("Identify Stationary & Mean-Reverting Series")), style={'margin-bottom': '20px'})
    
    input_ = dbc.Row([
        dbc.Col(create_dropdown('ticker-dropdown-1', names, ['EA', 'MD']), width=4),
        dbc.Col(create_date_picker('my-date-picker-range-1'), width="auto"),
        dbc.Col(
            dbc.Button("Submit", id="submit-button-1", color="primary"),
            width="auto",
            style={'overflow': 'visible', 'text-align': 'left'}
        )
    ], style={'margin-bottom': '10px'})
    res = dbc.Row([
            dbc.Col([
                html.Div(id='output-container-date-picker-range-1'),
                dcc.Graph(id='time-series-plot-1')
            ], width=8),
            dbc.Col([
                html.Div(id='numerical-data-1')
            ], width=4)
        ], style={'margin-bottom': '20px', 'display': 'flex'})
    
    
    return html.Div([title, input_, res])


def cluster_tickers():
    title = dbc.Row(dbc.Col(html.H2("Ticker Clustering")), style={'margin-bottom': '20px'})
    input_ = dbc.Row([
        dbc.Col(dcc.Dropdown(
                id='automatic-dropdown-1',
                options=[
                    {'label': 'Sector', 'value': 'Sector', 'search': 'Sector'},
                    {'label': 'Industry', 'value': 'Industry', 'search': 'Industry'},
                   #{'label': 'Market Cap', 'value': 'Market Cap', 'search': 'Market Cap'},
                    {'label': 'SOM', 'value': 'SOM', 'search': 'SOM Machine Learning Clustering Self Ordering Map'},
                    {'label': 'Random', 'value': 'Random', 'search': 'Random'}
                ],
                value='Industry',
                multi=False,
            ), width=2),
        dbc.Col(create_date_picker('my-date-picker-range-3'), width="auto"),
        create_button_with_loading("submit-button-3", "Cluster", "3"),
        dbc.Col(dcc.Dropdown(
                id='average-method-choice',
                options = [
                    {'label': 'Mean', 'value': 'Mean', 'search': 'Mean'},
                    {'label': 'Barycenters', 'value': 'Barycenters', 'search': 'Barycenters'}
                ],
                multi=False,
                value='Mean'
        ), width = 2),
        dbc.Col(dcc.Dropdown(
            id='dependent-dropdown',
            options=[],
        ), width=2),
        dbc.Col(
            dbc.Button("Plot", id="submit-button-4", color="primary"),
            width="auto",
            style={'overflow': 'visible', 'text-align': 'left'}
        )
    ], style={'margin-bottom': '10px'})
    res = dbc.Row([
                 dbc.Col([
                    dcc.Graph(id='cluster-plot-1')
                ], width=8),
                 dbc.Col([
                    dcc.Graph(id='bar-plot-1')
                ], width=4)
            ], style={'margin-bottom': '20px'})
    
    
    return html.Div([title, input_, res])


def pair_identification():
    title = dbc.Row(dbc.Col(html.H2("Pair Identification")), style={'margin-bottom': '20px'})
    input_ = dbc.Row([
        dbc.Col(dbc.Button(
            "Load", id="submit-button-6", color="primary"),
            width="auto",
            style={'overflow': 'visible', 'text-align': 'left'}
        ),
        dbc.Col([dcc.Dropdown(
            id = 'cluster-dropdown',
            options = [],
            placeholder = 'Select a computed cluster'
        )], width=4),
        dbc.Col([dcc.Dropdown(
            id = 'cluster-selection',
            options = [],
            placeholder = 'Select a cluster'
        )], width=3),
        dbc.Col(dbc.Button(
            "Submit", id="submit-button-5", color="primary"),
            width="auto",
            style={'overflow': 'visible', 'text-align': 'left'}
        ),
        dbc.Col(html.Div(id='pairs-success', children=''))
    ], style={'margin-bottom': '10px'})

    interim = dbc.Row([
                dbc.Col([
                    dbc.Progress(id='loading-bar', value=0, max=100, style={'width': '100%'}),
                    html.Div(id='time-taken', children='Time taken: 0s'),
                    html.Div(id='time-remaining', children='Time remaining: 0s')
                ], width=12)
            ], style={'margin-bottom': '20px'})

    load_res = dbc.Row([
        dbc.Col(dbc.Button(
            "Load", id="submit-button-8", color="primary"),
            width="auto",
            style={'overflow': 'visible', 'text-align': 'left'}
        ),
        dbc.Col([dcc.Dropdown(
            id = 'pairs-dropdown',
            options = [],
            placeholder = 'Select...'
        )], width=2),
        create_slider('slider-K', 10, 50, 1, 14),
        create_slider('slider-adf', 0, 1, 0.01, 1/3),
        create_slider('slider-hurst', 0, 1, 0.01, 1/3),
        create_slider('slider-coint', 0, 1, 0.01, 1/3),
        dbc.Col(dbc.Button(
            "Submit", id="submit-button-7", color="primary"
            ),
            width="auto",
            style={'overflow': 'visible', 'text-align': 'left'}
        )
    ])
    res = dbc.Row([
        dbc.Col([
                html.Div(id='pair-data-1')
            ], width=8),
            dbc.Col([
                dcc.Graph(id='pair-plot-1')
            ], width=4)
    ], style={'margin-bottom': '20px'})

    return html.Div([title, input_, interim, load_res, res])


def hedging_ratio(names):
    title = dbc.Row(dbc.Col(html.H2("Compute Hedging Ratio")), style={'margin-bottom': '20px'})
    
    input_ = dbc.Row([
            dbc.Col(create_dropdown('ticker-dropdown-2', names, ['EA', 'MD']), width=4),
            dbc.Col(create_date_picker('my-date-picker-range-2'), width="auto"),
            dbc.Col(
                dbc.Button("Submit", id="submit-button-2", color="primary"),
                width="auto",
                style={'overflow': 'visible', 'text-align': 'left'}
            ),
            dbc.Col(
    html.Div(
        html.H3(
            children="OLS: - | Kalman: - | Coint: -",
            style={
                "fontWeight": "bold",
                "white-space": "nowrap",
                "overflow": "hidden",
                "text-overflow": "ellipsis",
                "width": "100%"
            }
        ),
        id="insert-res"
    ),
    style={'margin-bottom': '10px'}
)
        ], style={'margin-bottom': '10px'})
    res = dbc.Row([
            dbc.Col([
                dcc.Graph(id='time-series-plot-3')
            ], width=8),
            dbc.Col([
                dcc.Graph(id='time-series-plot-2')
            ], width=4)
        ], style={'margin-bottom': '10px'})
    
    return html.Div([title, input_, res])
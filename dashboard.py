import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from datetime import date, datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from analytics_module.time_series import TimeSeries
from analytics_module.pair_analysis import KalmanRegression, OLSRegression, CointegrationTest
from data_loader.get_data import GetStockData


# Function to create dropdown
def create_dropdown(id, names, default_values):
    return dcc.Dropdown(
        id=id,
        options=[{'label': i, 'value': i.split(':', 1)[0]} for i in names],
        value=default_values,
        multi=True,
        style=dict(
                    width='40%',
                    verticalAlign="middle"
        )
    )

# Function to create date picker
def create_date_picker(id):
    return dcc.DatePickerRange(
        id=id,
        min_date_allowed=date(2013, 1, 1),
        max_date_allowed=datetime.today(),
        initial_visible_month=datetime.today(),
        start_date=datetime.today()-timedelta(days=61),
        end_date=datetime.today()-timedelta(days=31)
    )

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
data_fetcher = GetStockData()

tickers = data_fetcher.get_ticker_names()
names = []
for ticker in tickers:
    info = data_fetcher.get_ticker_field_info(ticker, field='longName')
    if info is not None:
        names.append(ticker +":"+ info)
    else:
        names.append(ticker)

app.layout = html.Div([
    dbc.Container([
        dbc.Row(dbc.Col(html.H1("Financial Analysis Dashboard"))),
        dbc.Row([
            dbc.Col([
                html.H2("Identify Stationary & Mean-Reverting Series"),
                create_dropdown('ticker-dropdown-1', names, ['AAPL', 'MSFT']),
                create_date_picker('my-date-picker-range-1'),
                html.Div(id='output-container-date-picker-range-1'),
                html.Button(id='submit-button-1', n_clicks=0, children='Submit'),
            ], width=4),
            dbc.Col([
                dcc.Graph(id='time-series-plot')
            ], width=8),
            dbc.Col([
                html.H2("Numerical Data"),
                html.Div(id='numerical-data')
            ], width=4)
        ]),
        dbc.Row([
            dbc.Col([
                html.H2("Compute Hedging Ratio"),
                create_dropdown('ticker-dropdown-2', names, ['AAPL', 'MSFT']),
                create_date_picker('my-date-picker-range-2'),
                html.Div(id='output-container-date-picker-range-2'),
                html.Button(id='submit-button-2', n_clicks=0, children='Submit'),
            ], width=4),
            dbc.Col([
                dcc.Graph(id='hedging-ratio-plot')
            ], width=8),
        ]),
    ], style={'width': '90%', 'max-width': 'none'}),
])



@app.callback(
    Output('ticker-dropdown-2', 'value'),
    Input('ticker-dropdown-2', 'value')
)
def limit_dropdown_selection(tickers):
    if len(tickers) > 2:
        return tickers[-2:]
    return tickers

@app.callback(
    Output('time-series-plot', 'figure'),
    [Input('ticker-dropdown-1', 'value')],
    Input('my-date-picker-range-1', 'start_date'),
    Input('my-date-picker-range-1', 'end_date')
)
def update_time_series_plot(tickers, s_date, e_date):
    print(tickers)
    try:
        start_date = datetime.strptime(s_date, "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d")
    except:
        start_date = s_date
    try:
        end_date = datetime.strptime(e_date, "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d")
    except:
        end_date = e_date

    # Fetch data
    data_fetcher.set_dates(start_date, end_date)
    fig = go.Figure()

    for ticker in tickers:
        df = data_fetcher.get_data(ticker)
        ts = df['close'].values

        # Create figure
        fig.add_trace(go.Scatter(x=df.index, y=ts, mode='lines', name=ticker))
        #fig.update_layout(title=f"{ticker} (Stationary: {is_stationary}/{p_value:.5f})      (Mean Reversion: {is_mean_reversion}/{h:.5f})", xaxis_title="Date", yaxis_title="Price")
    
    return fig

@app.callback(
    Output('numerical-data', 'children'),
    [Input('ticker-dropdown-1', 'value')],
    Input('my-date-picker-range-1', 'start_date'),
    Input('my-date-picker-range-1', 'end_date')
)
def update_numerical_data(tickers, s_date, e_date):
    # Fetch data and calculate metrics
    # ...
    # Test for stationarity
    try:
        start_date = datetime.strptime(s_date, "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d")
    except:
        start_date = s_date
    try:
        end_date = datetime.strptime(e_date, "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d")
    except:
        end_date = e_date

    cutoff = 0.05
    data_fetcher.set_dates(start_date, end_date)
    data = []
    n = max(0, -7+len(tickers))
    print(n)
    for ticker in tickers[n:]:
        sector = data_fetcher.get_ticker_field_info(ticker, field='sector')
        marketCap = data_fetcher.get_ticker_field_info(ticker, field='marketCap')
        df = data_fetcher.get_data(ticker)
        ts = df['close'].values
        if np.isnan(ts).any():
            is_stationary, p_value = False, '-'
            is_mean_reversion, h = False, '-'

        else:    
            data_analyzer = TimeSeries(ts, ticker)
            is_stationary, p_value = data_analyzer.check_for_stationarity(cutoff=cutoff)
            p_value = np.round(p_value,5)
            is_mean_reversion , h = data_analyzer.check_for_mean_reversion(cutoff=cutoff)
            h = np.round(h,5)

        marketCap = np.round(marketCap/1_000_000_000,2) if marketCap is not None else 0
        data.append({'Ticker': ticker, 'Market Cap/B': marketCap, 'Sector': sector, 'Hurst': h, 'ADF': p_value})

    # Create a DataTable
    table = dash_table.DataTable(
        data=data,
        columns=[{'name': 'Ticker', 'id': 'Ticker'},
                 {'name': 'Market Cap/B', 'id': 'Market Cap/B'},
                 {'name': 'Sector', 'id': 'Sector'},
                 {'name': 'Hurst', 'id': 'Hurst'},
                 {'name': 'ADF', 'id': 'ADF'}],
        style_cell={'textAlign': 'left'},
    )

    return table

@app.callback(
    Output('hedging-ratio-plot', 'figure'),
    [Input('ticker-dropdown-2', 'value')],
    Input('my-date-picker-range-2', 'start_date'),
    Input('my-date-picker-range-2', 'end_date')
)
def update_hedging_ratio_plot(tickers, s_date, e_date):
    try:
        start_date = datetime.strptime(s_date, "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d")
    except:
        start_date = s_date
    try:
        end_date = datetime.strptime(e_date, "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d")
    except:
        end_date = e_date
    # Parse tickers

    ticker1, ticker2 = tickers[-2:]

    # Fetch data
    df = data_fetcher.collate_dataset([ticker1, ticker2], start_date, end_date)
    df = df.pivot(columns='ticker', values='close')
    
    # Compute OLS hedging ratio
    ols = OLSRegression(df[ticker1], df[ticker2])
    ols_hedging_ratio = ols.cur_beta
    ols_hedging_const = ols.cur_alpha

    # Compute Kalman Filter hedging ratio
    kalman = KalmanRegression(df[ticker1], df[ticker2])
    kf_hedging_ratio = kalman.cur_beta
    kf_hedging_const = kalman.cur_alpha

    # Compute cointegration test
    coint = CointegrationTest(df[ticker1], df[ticker2])
    adf_coef = coint.cur_adf
    # Create figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[ticker2] * ols_hedging_ratio + ols_hedging_const, mode='lines', name=f"OLS {ticker2}"))
    fig.add_trace(go.Scatter(x=df.index, y=df[ticker2] * kf_hedging_ratio + kf_hedging_const, mode='lines', name=f"KF {ticker2}"))
    fig.add_trace(go.Scatter(x=df.index, y=df[ticker1], mode='lines', name=ticker1))
    fig.add_trace(go.Scatter(x=df.index, y=df[ticker2], mode='lines', name=ticker2))
    fig.update_layout(title=f"Hedging Ratio ({ticker1}/{ticker2})", xaxis_title="Date", yaxis_title="Price")
    fig.update_layout(title=f"{ticker1}/{ticker2} (Cointegration: {adf_coef:.5f})       (OLS Hedging Ratio: {ols_hedging_ratio:.5f})        (Kalman Hedging Ratio: {kf_hedging_ratio:.5f})", xaxis_title="Date", yaxis_title="Price")

    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
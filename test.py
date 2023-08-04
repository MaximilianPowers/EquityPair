from datetime import datetime, timedelta, date
from data_loader.get_data import GetStockData
from analytics_module.time_series import TimeSeries
from analytics_module.pair_analysis import KalmanRegression, OLSRegression, CointegrationTest
import numpy as np
import plotly.graph_objects as go

def update_time_series_plot(ticker, s_date, e_date):
    try:
        start_date = datetime.strptime(s_date, "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d")
    except:
        start_date = s_date
    try:
        end_date = datetime.strptime(e_date, "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d")
    except:
        end_date = e_date
    cutoff = 0.05

    # Fetch data
    data_fetcher = GetStockData()
    data_fetcher.set_dates(start_date, end_date)
    df = data_fetcher.get_data(ticker)
    ts = df['close'].values

    # Test for stationarity
    data_analyzer = TimeSeries(ts, ticker)
    is_stationary, p_value = data_analyzer.check_for_stationarity(cutoff=cutoff)
    p_value = np.round(p_value, 5)
    # Create figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=ts, mode='lines', name=ticker))
    fig.update_layout(title=f"{ticker} (Stationary: {is_stationary}/{p_value})", xaxis_title="Date", yaxis_title="Price")
    
    return fig

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
    ticker1, ticker2 = tickers.split(',')

    # Fetch data
    data_fetcher = GetStockData()
    df = data_fetcher.collate_dataset([ticker1, ticker2], start_date, end_date)
    df = df.pivot(columns='ticker', values='close')
    
    # Compute OLS hedging ratio
    ols = OLSRegression(df[ticker1], df[ticker2])
    ols_hedging_ratio = ols.cur_beta

    # Compute Kalman Filter hedging ratio
    kalman = KalmanRegression(df[ticker1], df[ticker2])
    

    kf_hedging_ratio = kalman.cur_beta

    # Create figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[ticker1] * ols_hedging_ratio, mode='lines', name=f"OLS {ticker1}"))
    fig.add_trace(go.Scatter(x=df.index, y=df[ticker1] * kf_hedging_ratio, mode='lines', name=f"KF {ticker1}"))
    fig.add_trace(go.Scatter(x=df.index, y=df[ticker2], mode='lines', name=ticker2))
    fig.update_layout(title=f"Hedging Ratio ({ticker1}/{ticker2})", xaxis_title="Date", yaxis_title="Price")
    
    return fig

fig = update_time_series_plot('PL', '2023-06-01', '2023-07-01')
import dash
from data_loader.get_data import GetStockData
from data_loader.misc_connect import MongoConnect
from gui.screen_1.layout import get_layout
from gui.screen_1.callbacks import register_callbacks
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Function to create dropdown
data_fetcher = GetStockData()
tickers = data_fetcher.get_ticker_names()
tickers = frozenset(tickers)
names = [ticker + ":" + (data_fetcher.get_ticker_field_info(ticker, field='longName') or ticker) for ticker in tickers]

m = MongoConnect()
app.layout = get_layout(names)
register_callbacks(app, data_fetcher, m)

if __name__ == '__main__':
    app.run_server(debug=True)
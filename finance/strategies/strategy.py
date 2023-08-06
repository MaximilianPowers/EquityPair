from analytics_module.time_series import TimeSeries
from analytics_module.pair_analysis import CointegrationTest
from datetime import datetime
from data_loader.get_data import GetStockData

g = GetStockData()
class PairTradingStrategy:
    def __init__(self, pairs, start_date_train, end_date_train, start_date_trade, end_date_trade, hyperparameters=None):
        self.pairs = pairs
        self.hyperparameters = hyperparameters or {}

        self.cache_df = {}
        self.ts = {
            "train": {},
            "trade": {}
        }

        self.pa = {
            "train": {},
            "trade": {}
        }
        self.start_date_train = start_date_train
        self.end_date_train = end_date_train
        self.start_date_trade = start_date_trade
        self.end_date_trade = end_date_trade

        self.initialize()

    def initialize(self):
        tickers = list(set([pair[0] for pair in self.pairs] + [pair[1] for pair in self.pairs]))
        print(tickers)
        self.cache_df["train"] = g.collate_dataset([tickers], self.start_date_train, self.end_date_train).pivot(columns='ticker', values='close')
        self.cache_df["trade"] = g.collate_dataset([tickers], self.start_date_trade, self.end_date_trade).pivot(columns='ticker', values='close')

        for pair in self.pairs:
            self.ts["train"][pair[0]+':'+[pair[1]]] = TimeSeries(self.cache_df["train"][pair[0]] - self.cache_df["train"][pair[1]])
            self.ts["trade"][pair[0]+':'+[pair[1]]] = TimeSeries(self.cache_df["trade"][pair[0]] - self.cache_df["trade"][pair[1]])

        for pair in self.pairs:
            self.pa["train"][pair[0]+':'+[pair[1]]] = CointegrationTest(self.cache_df["train"][pair[0]], self.cache_df["train"][pair[1]])



    def set_hyperparameters(self, hyperparameters):
        self.hyperparameters.update(hyperparameters)

    def execute_strategy(self):
        # Implement the trading logic here
        pass


pairs = [
    ("AAPL", "MSFT"),
    ("AAPL", "GOOG"),
    ("TSLA", "MSFT"),
    ("TSLA", "GOOG"),
    ("TSLA", "AAPL"),
    ("MSFT", "GOOG")
]

start_date_train = "2021-06-01"
end_date_train = "2022-07-1"
start_date_trade = "2022-07-2"
end_date_trade = "2023-07-1"



s = PairTradingStrategy(pairs, start_date_train, end_date_train, start_date_trade, end_date_trade)  

print(s.cache_df["train"])
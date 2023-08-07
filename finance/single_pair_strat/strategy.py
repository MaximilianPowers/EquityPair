from abc import ABC, abstractmethod
from data_loader.get_data import GetStockData
from finance.single_pair_strat.portfolio_single import SinglePairPortfolio
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class Strategy(ABC):
    def __init__(self, capital, ticker_1, ticker_2, start_training_date, end_training_date, start_date, end_date, hyperparameters = {}, ts=None):        

        self.ticker_1 = ticker_1
        self.ticker_2 = ticker_2
        self.cur_pos = 0 # 0 if no position, 1 if lng ticker_1 and short ticker 2, -1 if short ticker_1 and lng ticker_2
        self.hyperparameters = hyperparameters
        
        self.start_training_date = start_training_date
        self.end_training_date = end_training_date
        self.start_training_date_dt = self.str_to_date(self.start_training_date)
        self.end_training_date_dt = self.str_to_date(self.end_training_date)

        self.start_date = start_date        
        self.end_date = end_date
        self.start_date_dt = self.str_to_date(self.start_date)
        self.end_date_dt = self.str_to_date(self.end_date)

        if self.start_date_dt > self.end_date_dt:
            raise ValueError("start_date must be before end_date.")
        if self.start_training_date_dt > self.end_training_date_dt:
            raise ValueError("start_training_date must be before end_training_date.")
        if self.start_date_dt < self.start_training_date_dt:
            raise ValueError("start_date must be after start_training_date.")
        if ts is not None:
            self.ts = ts
        else:
            self.g = GetStockData()
            self.store_ticker_data()

        self.capital = capital
        records = self.ts.transpose().to_dict()
        self.portfolio = SinglePairPortfolio(capital, records)
        self.trade_open_date = None
        self.store_res = []

        # Must be set before buy or sell condition
        self.threshold_normal_buy = None 
        self.threshold_swapped_buy = None 
        self.threshold_normal_sell_low = None
        self.threshold_swapped_sell_low = None
        self.threshold_normal_sell_high = None
        self.threshold_swapped_sell_high = None

    def store_ticker_data(self):
        """
        Stores the time series data for the two tickers.
        """
        train_ticker_data = self.g.collate_dataset([self.ticker_1, self.ticker_2], self.start_training_date, self.end_training_date).pivot(columns='ticker', values='close')
        train_ticker_data["Mode"] = "Train"
        trade_ticker_data = self.g.collate_dataset([self.ticker_1, self.ticker_2], self.start_date, self.end_date).pivot(columns='ticker', values='close')
        trade_ticker_data["Mode"] = "Trade"
        self.ts = pd.concat([train_ticker_data, trade_ticker_data])
        self.ts.index = self.ts.index.strftime('%Y-%m-%d').tolist()


    def execute_trade(self, date, hedge_ratio):
        """
        Interface between strategies and portfolio to execute a trade.
        """
        self.portfolio.execute_pair_trade(self.cur_pos, self.ticker_1, self.ticker_2, date, hedge_ratio)
            
    def exit_position(self, date):
        """
        Interface between strategies and portfolio to exit out of a tradea trade.
        """
        self.portfolio.exit_pair_trade(self.trade_open_date, date)
            
        return False  

    def store_results(self, new_entry):
        self.store_res.append(new_entry)

    def plot_spread(self, labels):
        res = np.array(self.store_res)
        if res.shape[0] != len(labels):
            raise ValueError(f"Number of labels must match number of columns in results ({res.shape[0]}).")
        fig, ax = plt.subplots()
        for i in range(res.shape[1]):
            plt.plot(res[:, i], label=labels[i])
        plt.legend()
        ax.set_title("Kalman Filter Trading Strategy")
        ax.set_xlabel("Time")
        ax.legend(loc='upper right', bbox_to_anchor=(1.05, 1))
        plt.show()
    
    def post_trades(self, m):
        """
        Given a MongoDB connection, posts the history of trades to the database.
        """
        m.post_strategy_results(
            self.ticker_1, self.ticker_2, self.start_training_date, self.end_training_date, self.start_date, self.end_date,
            self.hyperparameters, self.portfolio.closed_trades
        )

    @abstractmethod
    def set_hyperparameters(self, hyperparameters):
        """
        Method to set or update hyperparameters.
        """
        pass

    @abstractmethod
    def train_model(self):
        """
        Method to train the model based on the training data.
        """
        pass
    
    @abstractmethod
    def update_model(self):
        """
        Method to update the model based on the current observation.
        """
        pass

    @abstractmethod
    def trade_model(self):
        """
        Method to trade the model based on the current observation.
        """
        pass

    @abstractmethod
    def buy_condition(self):
        """
        Method to define the buy condition based on ticker data and hyperparameters.
        Returns True if the buy condition is met, otherwise False.
        """
        pass

    @abstractmethod
    def sell_condition(self):
        """
        Method to define the sell condition based on ticker data and hyperparameters.
        Returns True if the sell condition is met, otherwise False.
        """
        pass


    @staticmethod
    def compute_threshold(mu, sigma, std_dev):
        return mu + sigma * std_dev, mu - sigma * std_dev

    @staticmethod
    def str_to_date(date_str):
        if date_str is not None and isinstance(date_str, str):
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            return None
    
    @staticmethod
    def date_to_str(date):
        if date is not None and isinstance(date, datetime):
            return date.strftime("%Y-%m-%d")
        else:
            return None
        


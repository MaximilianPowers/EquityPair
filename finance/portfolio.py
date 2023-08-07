
import matplotlib.pyplot as plt
class Portfolio(object):
    """
    A base class for pair trading strategies.
    """
    def __init__(self, capital, records, verbose=False):
        self.capital = capital
        self.records = records
        self.portfolio = {} # Key: Ticker, Value: Quantity
        self.pnl = 0.0
        self.open_trades = {}
        self.closed_trades = {}
        self.store_results = []
        self.portfolio_value = capital
        self.verbose = verbose

    def get_portfolio_value(self, date):
        """
        Returns the value of the portfolio.
        """
        value = self.capital
        for ticker in self.portfolio:
            value += self.portfolio[ticker] * self.records[date][ticker]
        return value 
    
    def _create_open_trade_record(self, long_ticker, short_ticker, long_quantity, short_quantity, date):
        return {
            "entry_date": date,
            "long_ticker": long_ticker,
            "short_ticker": short_ticker,
            "long_quantity": long_quantity,
            "short_quantity": short_quantity,
            "long_price": self.records[date][long_ticker],
            "short_price": self.records[date][short_ticker],
            "capital_remaining": self.capital
        }
    
    def _create_closed_trade_record(self, date, long_ticker, short_ticker, long_quantity, 
                short_quantity, exit_date, exit_price_long, exit_price_short, trade_pnl):
        return {
            "entry_date": date,
            "long_ticker": long_ticker,
            "short_ticker": short_ticker,
            "long_quantity": long_quantity,
            "short_quantity": short_quantity,
            "long_price": self.records[date][long_ticker],
            "short_price": self.records[date][short_ticker],
            "trade_exit_date": exit_date,
            "trade_exit_price_long": exit_price_long,
            "trade_exit_price_short": exit_price_short,
            "pnl": trade_pnl
        }
    
    def store_result(self, date):
        """
        Stores the results of the current trading period.
        """
        portfolio_value = self.get_portfolio_value(date)
        self.portfolio_value = portfolio_value
        self.store_results.append(portfolio_value)
    
    def plot_portfolio(self):
        """
        Plots the strategy over time, including entry and exit positions.
        """
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.plot(self.store_results)
        ax.set_xlabel("Date")
        ax.set_ylabel("Portfolio Value")
        plt.show()

        
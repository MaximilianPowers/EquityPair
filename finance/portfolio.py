from numpy import diff

class Portfolio(object):
    """
    A base class for pair trading strategies.
    """
    def __init__(self, capital, records, verbose=False):
        self.capital = capital
        self.starting_capital = capital
        self.prev_value = capital

        self.records = records
        self.cur_portfolio= {} # Key: Ticker, Value: Quantity
        self.store_portfolio = [] # Stores the portfolio value at each time step
        self.open_trades = {}
        self.closed_trades = {}

        self.store_portfolio_value = []
        self.stored_dates = []
        self.store_pnl = []
        self.return_series = None

        self.pnl = 0.0
        self.portfolio_value = capital
        self.verbose = verbose

    def get_portfolio_value(self, date):
        """
        Returns the value of the portfolio.
        """
        value = self.capital
        for ticker in self.cur_portfolio:
            value += self.cur_portfolio[ticker] * self.records[date][ticker]
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
    
    def _post_strategy_results(self):
        """
        Retrieve portfolio related metrics.
        """
        return {
            "starting_capital": self.starting_capital,
            "ending_capital": self.capital,
            "historic_returns": list(self.return_series),
            "historic_pnl": self.store_pnl,
            "track_portfolio": self.store_portfolio,
            "pnl": self.pnl,
            "growth": self.capital/self.starting_capital
        }
    
    def store_results(self, date):
        """
        Stores the results of the current trading period.
        """
        portfolio_value = self.get_portfolio_value(date)
        self.store_portfolio_value.append(portfolio_value)
        self.stored_dates.append(date)
        self.store_pnl.append(self.pnl)
        self.store_portfolio.append(self.cur_portfolio)

    def _set_return_series(self):
        """
        Returns the return series of the strategy.
        """
        values = self.store_portfolio_value
        self.return_series = diff(values) / values[:-1]

    

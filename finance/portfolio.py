from data_loader.get_data import GetStockData


g = GetStockData()

class PairTradingStrategy(object):
    """
    A trading strategy that executes trades based on signals
    and manages the portfolio.
    """
    def __init__(self, capital, max_alloc):
        self.capital = capital
        self.max_alloc = max_alloc
        self.portfolio = {} # Key: Ticker, Value: Quantity
        self.pnl = 0.0
        self.trades = []
        self.risk = 0.0

    def compute_risk(self):
        """
        Compute risk of the portfolio.
        """
        # Use your risk calculation model
        self.risk = 0.0
        for ticker, quantity in self.portfolio.items():
            # Risk calculation depends on your risk model
            # For simplicity, assume risk is proportional to quantity
            self.risk += abs(quantity)
    
    def execute_trade(self, ticker, quantity, date):
        """
        Execute a trade.
        """
        # Check capital constraints
        trade_value = quantity * g.get_single_date_price(ticker, date)
        if trade_value is None:
            raise Exception("Trade not executed due to missing price data.") 

        elif trade_value > self.capital:
            raise Exception("Trade not executed due to capital constraint.")
        
        # Execute trade
        self.portfolio[ticker] = self.portfolio.get(ticker, 0) + quantity
        self.capital -= trade_value
        self.pnl -= trade_value
        self.trades.append((ticker, quantity))
        
        # Update risk
        self.compute_risk()

    def close_position(self, ticker, date):
        """
        Close a position.
        """
        if ticker in self.portfolio:
            close_price = g.get_single_date_price(ticker, date)
            quantity = self.portfolio[ticker]
            self.pnl += quantity * close_price
            self.capital += quantity * close_price
            del self.portfolio[ticker]

    def check_signal(self, ticker, observations):
        """
        Check if there is a trading signal.
        """
        # Use your signal generation model
        spread = model.get_spread(observations)
        mean_spread = spread.mean()
        std_spread = spread.std()

        # Check for buy signal
        if spread.iloc[-1] < mean_spread - std_spread:
            return 'buy'
        # Check for sell signal
        elif spread.iloc[-1] > mean_spread + std_spread:
            return 'sell'
        else:
            return None
    
    def trade(self, ticker, observations, date):
        """
        Check for trading signal and execute trade if signal exists.
        """
        signal = self.check_signal(ticker, observations)
        if signal == 'buy':
            quantity = self.capital * self.max_alloc / g.get_single_date_price(ticker, date)
            self.execute_trade(ticker, quantity)
        elif signal == 'sell':
            self.close_position(ticker)
from finance.portfolio import Portfolio
MAX_TOL = .1
class SinglePairPortfolio(Portfolio):
    """
    A trading strategy that executes trades based on signals
    and manages the portfolio.
    """
    def __init__(self, capital, records, tol = MAX_TOL):
        super().__init__(capital, records)
        self.tol = tol


    def execute_pair_trade(self, pos, ticker_y, ticker_x, date, hedging_ratio):
        price_ticker_x = self.records[date][ticker_x]
        price_ticker_y = self.records[date][ticker_y]

        quantity_ticker_x = (self.tol * self.capital) / (price_ticker_x + hedging_ratio * price_ticker_y)
        quantity_ticker_y = quantity_ticker_x * hedging_ratio
        long_ticker, short_ticker, long_quantity, short_quantity = self._determine_positions(
            pos, ticker_y, ticker_x, quantity_ticker_y, quantity_ticker_x)

        # Update portfolio
        self._update_portfolio(long_ticker, short_ticker, long_quantity, short_quantity, date)

        # Record the trade
        self.open_trades[date] = self._create_open_trade_record(
            long_ticker, short_ticker, long_quantity, short_quantity, date)

    def _determine_positions(self, pos, ticker_y, ticker_x, quantity_ticker_y, quantity_ticker_x):
        if pos == 1:
            return ticker_y, ticker_x, quantity_ticker_y, quantity_ticker_x
        elif pos == -1:
            return ticker_x, ticker_y, quantity_ticker_x, quantity_ticker_y
        else:
            raise ValueError("pos must be 1 or -1, (long short)/(short long)")
    
    def _update_portfolio(self, long_ticker, short_ticker, long_quantity, short_quantity, date):
        long_cost = long_quantity * self.records[date][long_ticker]
        # Calculate the proceeds from selling the short position
        short_proceeds = short_quantity * self.records[date][short_ticker]

        # Update the portfolio quantities
        self.portfolio[long_ticker] = self.portfolio.get(long_ticker, 0) + long_quantity
        self.portfolio[short_ticker] = self.portfolio.get(short_ticker, 0) - short_quantity

        # Update the capital by subtracting the long cost and adding the short proceeds
        self.capital -= long_cost - short_proceeds
        if self.verbose:
            print("Capital after bought stock:")
            print(f"Long {long_ticker}: {long_quantity * self.records[date][long_ticker]}")
            print(f"Short {short_ticker}: {short_quantity * self.records[date][short_ticker]}")
            print(f"Capital: {self.capital}")
            print("-"*50)


    def exit_pair_trade(self, enter_date, exit_date):
        trade = self.open_trades[enter_date]
        entry_price_long = trade["long_price"]
        entry_price_short = trade["short_price"]
        exit_price_long = self.records[exit_date][trade["long_ticker"]]
        exit_price_short = self.records[exit_date][trade["short_ticker"]]

        # Calculate the value of the long and short positions at exit
        long_value_exit = trade["long_quantity"] * exit_price_long
        short_value_exit = trade["short_quantity"] * exit_price_short

        # Calculate the profit/loss from the trade
        val = trade["long_quantity"] * (exit_price_long - entry_price_long) - \
            trade["short_quantity"] * (exit_price_short - entry_price_short)

        # Update the PnL and the capital
        self.pnl += val
        self.capital += long_value_exit - short_value_exit

        # Update the portfolio quantities
        self.portfolio[trade["long_ticker"]] -= trade["long_quantity"]
        self.portfolio[trade["short_ticker"]] += trade["short_quantity"]
        if self.verbose:
            print("Capital after sold stock:")
            print(f"Long {trade['long_ticker']}: {trade['long_quantity'] * exit_price_long}")
            print(f"Short {trade['short_ticker']}: {trade['short_quantity'] * exit_price_short}")
            print(f"Capital: {self.capital}")
            print(f"Profit: {val}")
            print("-"*50)
        
        self.closed_trades[enter_date + ':' + exit_date] = self._create_closed_trade_record( \
            enter_date, trade["long_ticker"], trade["short_ticker"], trade["long_quantity"],\
            trade["short_quantity"], exit_date, exit_price_long, exit_price_short, val)
        del self.open_trades[enter_date]



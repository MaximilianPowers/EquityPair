# Post strategy interface interacting with MongoDB "strategy_results"

import numpy as np

class PostTradeMetrics:
    def __init__(self, ticker_1, ticker_2, start_date, end_date):
        self.ticker_1 = ticker_1
        self.ticker_2 = ticker_2
        self.start_date_trade = start_date
        self.end_date_trade = end_date


    def initialise_portfolio(self, starting_capital, daily_pnl, pnl, growth):
        self.starting_capital = starting_capital
        if isinstance(daily_pnl, list):
            daily_pnl = np.array(daily_pnl)
        self._set_return_series(daily_pnl)
        self.pnl = pnl
        self.growth = growth
        self.final_capital = starting_capital + pnl
    
    def initialise_trades(self, closed_trades):
        self.closed_trades = closed_trades

    
    def calculate_sharpe_ratio(self, rr, returns_series=None):
        """
        Calculates the Sharpe ratio of the strategy.
        """
        if returns_series is None:
            returns_series = self.return_series
        std_dev = np.std(returns_series)
        d_rr = rr / 252 # Assuming 252 trading days in a year
        if std_dev < 1e-4:  # Handle the case when standard deviation is zero
            return 0
        
        mean_return = np.mean(returns_series)
        return (mean_return - d_rr) / std_dev


    
    def calculate_max_drawdown(self, returns_series=None):
        if returns_series is None:
            returns_series = self.return_series
        cumulative_returns = np.cumprod(1 + returns_series) - 1
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = running_max - cumulative_returns
        max_drawdown = np.max(drawdowns)

        return max_drawdown

    def calculate_calmar_ratio(self, returns_series=None):
        if returns_series is None:
            returns_series = self.return_series

        avg_annual_return = np.mean(returns_series) * 252 # Assuming 252 trading days in a year
        max_drawdown = self.calculate_max_drawdown(returns_series)

        if max_drawdown < 1e-5:
            return 0

        return avg_annual_return / max_drawdown

    def calculate_sortino_ratio(self, rr, target_return=0.0, returns_series=None):
        if returns_series is None:
            returns_series = self.return_series
        d_tr = target_return / 252 # Assuming 252 trading days in a year
        d_rr = rr / 252 # Assuming 252 trading days in a year
        mean_return = np.mean(returns_series)
        negative_returns = [ret - d_tr for ret in returns_series if ret < d_tr]
        downside_deviation = np.sqrt(np.mean(np.square(negative_returns))) if negative_returns else 0

        if downside_deviation < 1e-5:
            return 0

        return (mean_return - d_rr) / downside_deviation
    
    def historic_sharpe_ratio(self, rr=0.1):
        sharpe_ratios = [0, 0]

        for indx in range(2, len(self.return_series)): # Start from 2 to avoid std = 2
            sharpe_ratios.append(self.calculate_sharpe_ratio(rr, self.return_series[:indx]))

        return sharpe_ratios
    
    def historic_calmar_ratio(self):
        calmar_ratios = []

        for indx in range(1, len(self.return_series) + 1):
            calmar_ratios.append(self.calculate_calmar_ratio(self.return_series[:indx]))

        return calmar_ratios

    def historic_sortino_ratio(self, rr=0.1, target_return=0.0):
        sortino_ratios = []

        for indx in range(1, len(self.return_series) + 1):
            sortino_ratios.append(self.calculate_sortino_ratio(rr, target_return, self.return_series[:indx],))

        return sortino_ratios

    def historic_max_drawdown(self):
        max_drawdowns = []

        for indx in range(1, len(self.return_series) + 1):
            max_drawdowns.append(self.calculate_max_drawdown(self.return_series[:indx]))

        return max_drawdowns
    
    def _set_return_series(self, daily_pnl):
        """
        Returns the return series of the strategy.
        """
        daily_changes_pnl = np.diff(daily_pnl)

        prev_pnl_nonzero = np.where(daily_pnl[:-1] == 0, 1, daily_pnl[:-1])

        daily_returns = daily_changes_pnl / prev_pnl_nonzero

        daily_returns[prev_pnl_nonzero == 1] = 0
        self.return_series = daily_returns
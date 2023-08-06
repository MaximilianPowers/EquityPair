import numpy as np
from scipy.optimize import minimize
from data_loader.get_data import GetStockData

g = GetStockData()
class AllocatePortfolio:
    def __init__(self, pairs, start_date, end_date, risk_free_rate=0.01):
        self.pairs = pairs
        self.start_date = start_date
        self.end_date = end_date
        self.risk_free_rate = risk_free_rate
        self.data = self.fetch_data()

    def fetch_data(self):
        unique_tickers = []
        for ticker_1, ticker_2 in self.pairs:
            unique_tickers.append(ticker_1)
            unique_tickers.append(ticker_2)
        unique_tickers = list(set(unique_tickers))
        return g.collate_dataset([unique_tickers], self.start_date, self.end_date).pivot(columns='ticker', values='close')

    def calculate_risk(self, weights, pair_data):
        returns = np.log(pair_data / pair_data.shift(1))
        portfolio_stddev = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        return portfolio_stddev

    def calculate_sharpe(self, weights, pair_data):
        returns = np.log(pair_data / pair_data.shift(1))
        portfolio_return = np.sum(returns.mean() * weights) * 252
        portfolio_stddev = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_stddev
        return -sharpe_ratio  # Minimize the negative Sharpe ratio

    def calculate_sortino(self, weights, pair_data):
        returns = np.log(pair_data / pair_data.shift(1))
        portfolio_return = np.sum(returns.mean() * weights) * 252
        downside_returns = returns.copy()
        downside_returns[downside_returns > 0] = 0
        downside_stddev = np.sqrt(np.sum(downside_returns**2) / len(downside_returns))
        sortino_ratio = (portfolio_return - self.risk_free_rate) / downside_stddev
        return -sortino_ratio  # Minimize the negative Sortino ratio

    def minimize_risk(self, pair, metric='risk'):
        
        num_assets = len(pair.columns)
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        constraints = ({'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1})
        bounds = tuple((0, 1) for asset in range(num_assets))
        
        if metric == 'sharpe':
            objective = self.calculate_sharpe
        elif metric == 'sortino':
            objective = self.calculate_sortino
        else:
            objective = self.calculate_risk
        
        solution = minimize(objective, weights, args=(self.data[[pair[0], pair[1]]],), method='SLSQP', bounds=bounds, constraints=constraints)
        return solution.x

    def allocate(self, metric='risk'):
        # TODO: Implement edge case where same ticker appears in two different pairs, i.e. if the strategy has selected
        # (APPL, MSFT) and (APPL, AMZN).

        allocation = {}
        for pair in self.pairs:
            allocation[pair] = self.minimize_risk(pair, metric)
        return allocation


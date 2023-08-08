from finance.single_pair_strat.strategy import Strategy
from numpy import isnan, sqrt
from analytics_module.pair_analysis import KalmanRegression, OLSRegression
# SET DEFAULT BUY/SELL CONDITION HYPERPARAMETERS
BASE_BUY_SIGMA = 1 
BASE_SELL_SIGMA_LOW = 0.5
BASE_SELL_SIGMA_HIGH = 2
BASE_MAXLEN = 3000


class OnlineRegressionStrategy(Strategy):
    """
    Class for a Kalman filter based trading strategy for a single pair of equities.
    Based off the model that ticker_1 = ticker_2*alpha + beta
    """
    def __init__(self, method, capital, ticker_1, ticker_2, start_training_date, end_training_date, start_date, end_date, hyperparameters = {}, time_series = None):
        if method not in ["KalmanRegression", "OLSRegression"]:
            raise ValueError("method must be either KalmanRegression or OLSRegression.")
        self.method_name = method
        super().__init__(capital, ticker_1, ticker_2, start_training_date, end_training_date, start_date, end_date, hyperparameters, time_series)
        self.set_hyperparameters(hyperparameters)

        self.ts = self.ts.dropna()
        self.time_series_1 = self.ts[self.ts["Mode"] == "Train"][self.ticker_1]
        self.time_series_2 = self.ts[self.ts["Mode"] == "Train"][self.ticker_2]

        self.count = len(self.time_series_1.index)

        if method == 'KalmanRegression':
            self.method = KalmanRegression(self.time_series_1, self.time_series_2, 
                                       maxlen = self.hyperparameters["maxlen"])           
        elif method == 'OLSRegression':
            self.method = OLSRegression(self.time_series_1, self.time_series_2, 
                                       maxlen = self.hyperparameters["maxlen"])
    

    def set_hyperparameters(self, hyperparameters):
        """
        Sets the hyperparameters for the strategy. We use 
        buy_sigma to determine the buy threshold, and sell_sigma_low and sell_sigma_high 
        to determine the sell thresholds (if spread returns below or exceeds the tolerance).

        Parameters
        ----------
        hyperparameters : dict

        Returns
        -------
        None.
        """
        self.hyperparameters["buy_sigma"] = hyperparameters.get("buy_sigma", BASE_BUY_SIGMA)
        self.hyperparameters["sell_sigma_high"] = hyperparameters.get("sell_sigma_high", BASE_SELL_SIGMA_HIGH)
        self.hyperparameters["sell_sigma_low"] = hyperparameters.get("sell_sigma_low", BASE_SELL_SIGMA_LOW)
        if self.hyperparameters["sell_sigma_high"] < self.hyperparameters["sell_sigma_low"]:
            raise ValueError("sell_sigma_high must be greater than sell_sigma_low.")
        if self.hyperparameters["buy_sigma"] < self.hyperparameters["sell_sigma_low"]:
            raise ValueError("buy_sigma must be greater than sell_sigma_low.")
        
        self.hyperparameters["maxlen"] = hyperparameters.get("maxlen", BASE_MAXLEN)

    def train_model(self):
        self.method.run()
        tmp = self.time_series_2 - self.method.cur_beta*self.time_series_1  - self.method.cur_alpha
        self.mu_hist = tmp.mean()
        self.var_hist = tmp.var()
        self.n = len(tmp)
        std_dev = sqrt(self.var_hist)
        self.threshold_normal_buy, self.threshold_swapped_buy = self.compute_threshold(self.mu_hist, self.hyperparameters["buy_sigma"], std_dev)
        self.threshold_normal_sell_low, self.threshold_swapped_sell_low = self.compute_threshold(self.mu_hist, self.hyperparameters["sell_sigma_low"], std_dev)
        self.threshold_normal_sell_high, self.threshold_swapped_sell_high = self.compute_threshold(self.mu_hist, self.hyperparameters["sell_sigma_high"], std_dev)

    def update_threshold(self, observation):
        # Update threshold with Welford's algorithm
        spread =self.method.get_spread(observation) # Calculate spread
        self.n += 1
        delta = spread - self.mu_hist
        self.mu_hist += delta / self.n
        delta2 = spread - self.mu_hist
        self.var_hist = ((self.n - 1) * self.var_hist + delta * delta2) / self.n
        std_dev = sqrt(self.var_hist)
        
        self.threshold_normal_buy, self.threshold_swapped_buy = self.compute_threshold(self.mu_hist, self.hyperparameters["buy_sigma"], std_dev)
        self.threshold_normal_sell_low, self.threshold_swapped_sell_low = self.compute_threshold(self.mu_hist, self.hyperparameters["sell_sigma_low"], std_dev)
        self.threshold_normal_sell_high, self.threshold_swapped_sell_high = self.compute_threshold(self.mu_hist, self.hyperparameters["sell_sigma_high"], std_dev)

    def update_model(self, observation):
        self.method.update(observation)
        self.update_threshold(observation)
    
    def trade_model(self):
        
        portfolio_value = self.capital
        observations = self.ts[self.ts["Mode"] == "Trade"][[self.ticker_1, self.ticker_2]].values
        dates = self.ts[self.ts["Mode"] == "Trade"].index
        for indx, observation in enumerate(observations):
            if observation is None:
                continue
            if observation[0] is None or observation[1] is None:
                continue
            if isnan(observation[0]) or isnan(observation[1]):
                continue
            self.store_results([
                    self.threshold_normal_buy,
                    self.threshold_swapped_buy,
                    self.threshold_normal_sell_low,
                    self.threshold_swapped_sell_low,
                    self.threshold_normal_sell_high,
                    self.threshold_swapped_sell_high,
                    self.method.get_spread(observation),
            ])
            date = dates[indx]
            observation = (observation[0], observation[1])
            if self.cur_pos == 0:
                buy_1, buy_2 = self.buy_condition(observation)
                if buy_1 and not buy_2:
                    self.cur_pos = 1

                elif buy_2 and not buy_1:
                    self.cur_pos = -1

                if buy_1 or buy_2:
                    self.execute_trade(date, self.method.cur_beta)
                    self.update_model(observation)
                    self.trade_open_date = date
                    continue
            else:
                sell = self.sell_condition(observation)
                if sell:
                    self.exit_position(date)
                    self.trade_open_date = None
                    self.cur_pos = 0
            self.portfolio.store_result(date)
            portfolio_value = self.portfolio.portfolio_value
            if portfolio_value < 0:
                print("Portfolio value is negative. You're broken. Exiting.")
                break
            self.update_model(observation)

        if self.cur_pos != 0:
            # Close out of all positions at the end of the trading period
            self.exit_position(date)
            self.trade_open_date = None
            self.cur_pos = 0
        if False:
            self.portfolio.plot_portfolio()


    def buy_condition(self, observation):
        #TODO Turn these into a class with options methods
        if self.cur_pos != 0:
            return False, False

        if self.method.get_spread(observation) > self.threshold_normal_buy:
            return True, False
        if self.method.get_spread(observation) < self.threshold_swapped_buy:
            return False, True
        else:
            return False, False
        
    def sell_condition(self, observation):
        #TODO Turn these into a class with options methods
        if self.cur_pos == 0:
            return False
        
        if self.cur_pos == 1:
            if self.method.get_spread(observation) < self.threshold_normal_sell_low:
                return True
            if self.method.get_spread(observation) > self.threshold_normal_sell_high:
                return True
        if self.cur_pos == -1:
            if self.method.get_spread(observation) > self.threshold_swapped_sell_low:
                return True
            if self.method.get_spread(observation) < self.threshold_swapped_sell_high:
                return True




            


        

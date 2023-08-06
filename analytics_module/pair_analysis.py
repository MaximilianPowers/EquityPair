import numpy as np
import pandas as pd
from filterpy.kalman import KalmanFilter
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller

class OnlineRegression(object):
    """
    Parent class for online regression models, requires there to be an update
    and spread function.
    """

    def __init__(self, ts1, ts2):
        self._x = ts2.name
        self._y = ts1.name

    def run(self):
        """
        Runs the first time for a set window_size.
        """
        raise NotImplementedError()
    
    def update(self, observations):
        """
        To run when in online mode beyond the window size.
        """
        raise NotImplementedError()

    def get_spread(self, observations):
        """
        During online mode, returns the spread between the prediction and actual value.
        """
        raise NotImplementedError()

    def plot_parameters(self):
        plt.figure(figsize=(14, 7))

        plt.subplot(2, 1, 1)
        plt.plot(self.means.index, self.means['beta'], label='beta')
        plt.title('Evolution of Beta over Time')
        plt.legend()

        plt.subplot(2, 1, 2)
        plt.plot(self.means.index, self.means['alpha'], label='alpha', color='orange')
        plt.title('Evolution of Alpha over Time')
        plt.legend()

        plt.tight_layout()
        plt.show()

class KalmanRegression(OnlineRegression):
    """
    Uses a Kalman Filter to estimate regression parameters 
    in an online fashion.
    Estimated model: ts1 ~ beta * ts2 + alpha
    """
    def __init__(self, ts1, ts2, delta=1e-5, maxlen=3000):
        super().__init__(ts1, ts2)
        self.maxlen = maxlen
        self.ts1 = ts1
        trans_cov = delta / (1 - delta) * np.eye(2)
        obs_mat = [np.array([[x, 1.0]]) for x in ts2.values]
        self.kf = KalmanFilter(dim_x=2, dim_z=1)
        self.kf.x = np.zeros(2)
        self.kf.P = np.eye(2)
        self.kf.F = np.eye(2)
        self.kf.H = obs_mat
        self.kf.R = 1
        self.kf.Q = trans_cov
        
    def set_observation_matrix(self, ts2):
        self.kf.H = [np.array([[x, 1.0]]) for x in ts2.values]

    def run(self):
        (state_means, state_covs, _, _) = self.kf.batch_filter(self.ts1.values, Hs=self.kf.H)
        self.means = pd.DataFrame(state_means, 
                                  index=self.ts1.index, 
                                  columns=['beta', 'alpha'])
        self.cur_beta = state_means[-1][0]
        self.cur_alpha = state_means[-1][1]
        self.state_cov = state_covs[-1]

    def update(self, observations):
        x = observations[self._x]
        y = observations[self._y]
        self.kf.H = np.array([[x, 1.0]])
        self.kf.predict()
        mu, self.state_cov = self.kf.update(y)
        mu = pd.Series(mu, index=['beta', 'alpha'], 
                       name=observations.name)
        self.means = self.means.append(mu)
        self.cur_beta = self.mean[-1][0]
        self.cur_alpha = self.mean[-1][1]
        if self.means.shape[0] > self.maxlen:
            self.means = self.means.iloc[-self.maxlen:]

    def get_spread(self, observations):
        x = observations[self._x]
        y = observations[self._y]
        return y - (self.means.beta[-1] * x + self.means.alpha[-1])

    @property
    def state_mean(self):
        return self.means.iloc[-1]


class OLSRegression(OnlineRegression):
    """
    Uses ordinary least squares (OLS) regression to estimate regression parameters 
    in an online fashion.
    Estimated model: ts2 ~ beta * ts2 + alpha
    """
    def __init__(self, ts1, ts2, maxlen=3000):
        super().__init__(ts1, ts2)
        self.maxlen = maxlen
        self.data = pd.DataFrame({self._x: ts2, self._y: ts1})

    def run(self):
        self.model = OLS(self.data[self._y], add_constant(self.data[self._x]))
        self.results = self.model.fit()
        self.cur_beta = self.results.params[1]
        self.cur_alpha = self.results.params[0]


    def update(self, observations):
        new_obs = pd.DataFrame({self._x: [observations[self._x]], 
                                self._y: [observations[self._y]]})
        self.data = pd.concat([self.data, new_obs])
        if self.data.shape[0] > self.maxlen:
            self.data = self.data.iloc[-self.maxlen:]
        self.model = OLS(self.data[self._y], add_constant(self.data[self._x]))
        self.results = self.model.fit()
        self.cur_beta = self.results.params[1]
        self.cur_alpha = self.results.params[0]



    def get_spread(self, observations):
        x = observations[self._x]
        y = observations[self._y]
        predicted_y = self.results.params['const'] + self.results.params[self._x] * x
        return y - predicted_y

class CointegrationTest(OnlineRegression):
    """
    Tests for cointegration between two time series using the Augmented Dickey-Fuller test.
    """
    def __init__(self, ts1, ts2):
        super().__init__(ts1, ts2)
        self.data = pd.DataFrame({self._x: ts2, self._y: ts1})
    
    def run(self):
        self.model = OLS(self.data[self._y], add_constant(self.data[self._x]))
        self.results = self.model.fit()
        self.residuals = self.results.resid

        adf_result = adfuller(self.residuals)
        self.adf_pvalues = [adf_result[1]]
        self.cur_adf = self.adf_pvalues[-1]

    def update(self, observations):
        new_obs = pd.DataFrame({self._x: [observations[self._x]], 
                                self._y: [observations[self._y]]})
        self.data = pd.concat([self.data, new_obs])
        self.model = OLS(self.data[self._y], add_constant(self.data[self._x]))
        self.results = self.model.fit()
        self.residuals = self.results.resid

        adf_result = adfuller(self.residuals)
        self.adf_pvalues.append(adf_result[1])
        self.cur_adf = self.adf_pvalues[-1]

    def is_cointegrated(self, cut_off=0.05):
        if not self.adf_pvalues:
            raise Exception("No updates made yet, cannot determine cointegration.")
        # Returns True if the most recent ADF p-value is less than the significance level
        return self.adf_pvalues[-1] < cut_off, self.adf_pvalues[-1]
    
    def spread(self):
        return self.residuals
    
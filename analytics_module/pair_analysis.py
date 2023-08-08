import numpy as np
import pandas as pd
from filterpy.kalman import KalmanFilter
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from collections import deque

class OnlineRegression(object):
    """
    Parent class for online regression models, requires there to be an update
    and spread function.
    """

    def __init__(self, ts1, ts2):
        self._x = ts2.name
        self._y = ts1.name

        self.cur_alpha = None
        self.cur_beta = None

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
    Estimated model: ts2 ~ beta * ts1 + alpha
    """
    def __init__(self, ts1, ts2, delta=1e-5, maxlen=3000):
        super().__init__(ts1, ts2)
        self.maxlen = maxlen
        self.ts2 = ts2
        trans_cov = delta / (1 - delta) * np.eye(2)
        obs_mat = [np.array([[x, 1.0]]) for x in ts1.values]
        self.kf = KalmanFilter(dim_x=2, dim_z=1)
        self.kf.x = np.zeros(2)
        self.kf.P = np.eye(2)
        self.kf.F = np.eye(2)
        self.kf.H = obs_mat
        self.kf.R = 1
        self.kf.Q = trans_cov
        self.means = deque(maxlen=self.maxlen)
        
    def set_observation_matrix(self, ts1):
        self.kf.H = [np.array([[x, 1.0]]) for x in ts1.values]

    def run(self):
        (state_means, state_covs, _, _) = self.kf.batch_filter(self.ts2.values, Hs=self.kf.H)
        self.means.extend(state_means)
        self.cur_beta = state_means[-1][0]
        self.cur_alpha = state_means[-1][1]
        self.state_cov = state_covs[-1]

    def update(self, observation):
        x, y = observation
        self.kf.H = np.array([[x, 1.0]])
        self.kf.predict()
        self.kf.update(y)
        mu, self.state_cov = self.kf.x, self.kf.P 

        self.means.append([mu[0], mu[1]])
        self.cur_beta = self.means[-1][0]
        self.cur_alpha = self.means[-1][1]

    def get_spread(self, observation):
        x, y = observation
        return y - (self.cur_beta * x + self.cur_alpha)



class OLSRegression(OnlineRegression):
    """
    Uses ordinary least squares (OLS) regression to estimate regression parameters 
    in an online fashion.
    Estimated model: ts1 ~ beta * ts2 + alpha
    """
    def __init__(self, ts1, ts2, maxlen=3000):
        super().__init__(ts1, ts2)
        self.maxlen = maxlen
        self.ts1 = deque(ts1, maxlen=self.maxlen)
        self.ts2 = deque(ts2, maxlen=self.maxlen)

    def run(self):
        data = pd.DataFrame({self._x: list(self.ts1), self._y: list(self.ts2)}) # Swap ts1 and ts2
        self.model = OLS(data[self._y], add_constant(data[self._x])) # Swap x and y
        self.results = self.model.fit()
        self.cur_alpha, self.cur_beta = self.results.params

    def update(self, observation):
        x, y = observation
        self.ts2.append(y) # x corresponds to ts1
        self.ts1.append(x) # y corresponds to ts2
        self.run()  # Re-run the model


    def get_spread(self, observations):
        x, y = observations
        predicted_y = self.cur_alpha + self.cur_beta * x
        return y - predicted_y
    
class CointegrationTest(OnlineRegression):
    """
    Tests for cointegration between two time series using the Augmented Dickey-Fuller test.
    """
    def __init__(self, ts1, ts2, maxlen=3000):
        super().__init__(ts1, ts2)
        self.maxlen = maxlen
        self.ts1 = deque(ts1, maxlen=self.maxlen)
        self.ts2 = deque(ts2, maxlen=self.maxlen)

    def run(self):
        data = pd.DataFrame({self._x: list(self.ts1), self._y: list(self.ts2)}) # Swap ts1 and ts2
        self.model = OLS(data[self._y], add_constant(data[self._x])) # Swap x and y
        self.results = self.model.fit()
        self.residuals = self.results.resid

        adf_result = adfuller(self.residuals)
        self.adf_pvalues = [adf_result[1]]
        self.cur_adf = self.adf_pvalues[-1]

    def update(self, observations):
        x, y = observations
        self.ts2.append(y) 
        self.ts1.append(x) 
        self.run() 

    def is_cointegrated(self, cut_off=0.05):
        if not self.adf_pvalues:
            raise Exception("No updates made yet, cannot determine cointegration.")
        # Returns True if the most recent ADF p-value is less than the significance level
        return self.adf_pvalues[-1] < cut_off, self.adf_pvalues[-1]
    
    def spread(self):
        return np.sum(self.residuals)
    
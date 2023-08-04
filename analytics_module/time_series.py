import numpy as np
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt

class TimeSeries:
    def __init__(self, time_series, ticker):
        self.ticker = ticker
        self.ts = time_series

    def plot(self):
        """
        Plots the time series.
        """
        fig, ax = plt.subplots(figsize=(15, 7))
        ax.plot(self.ts, label=self.ticker)
        ax.legend()

        return fig, ax
    
    def mean_reversion_test(self, MAX_LAG=4):
        """
        Tests whether or not a time series is mean reverting using the Hurst exponent
        """
        lags = range(2, min(len(self.ts)//5 + 1, MAX_LAG))
        variancetau = []
        tau = []
        for lag in lags: 

            tau.append(lag)
            pp = np.subtract(self.ts[lag:], self.ts[:-lag])
            variancetau.append(np.var(pp))
        m = np.polyfit(np.log10(tau),np.log10(variancetau),1)

        hurst = m[0] / 2

        return hurst

    def check_for_stationarity(self, cutoff=0.01):
        """
        Tests whether the time series are stationary using the Augmented Dickey-Fuller test.
        """
        pvalue = adfuller(self.ts)[1]
        if pvalue < cutoff:
            return True, pvalue
        else:
            return False, pvalue
    
    def check_for_mean_reversion(self, cutoff=0.5):
        hurst = self.mean_reversion_test()
        if hurst < cutoff:
            return True, hurst
        else:
            return False, hurst
        



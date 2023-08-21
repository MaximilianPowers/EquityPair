from analytics.time_series import TimeSeries
from analytics.regression import CointegrationTest
from tqdm import tqdm


class IdentifyCandidates:
    def __init__(self, ticker_pairs, time_series_data_frame, max_lag=None, hurst_cutoff=0.5, adf_cutoff=0.01, coint_cutoff=0.01):

        self.ticker_pairs = ticker_pairs
        self.df = time_series_data_frame
        self.score = {}

        # Hyper-parameters
        if max_lag is None:
            self.max_lag = max(len(self.df.index)//5 + 1, 4)
        else:
            self.max_lag = max_lag
        self.hurst_cutoff = hurst_cutoff
        self.adf_cutoff = adf_cutoff
        self.coint_cutoff = coint_cutoff


    def iterate_tickers(self):
        for ticker_1, ticker_2 in tqdm(self.ticker_pairs):
            comb = ticker_1 + ':' + ticker_2

            mask = self.df[ticker_2].notna() & self.df[ticker_1].notna()

            ts_vals = self.df[ticker_1][mask].values - self.df[ticker_2][mask].values
            if len(ts_vals) < len(self.df.index)*0.1:
                continue
            pa = CointegrationTest(self.df[ticker_1][mask], self.df[ticker_2][mask], maxlen=10)
            pa.run()
            ts = TimeSeries(ts_vals)
            _, c_pvalue = pa.is_cointegrated(self.coint_cutoff)
            _, s_pvalue, _, hurst = ts.run_full_test(self.adf_cutoff, self.hurst_cutoff, self.max_lag)
            self.score[comb] = {}
            
            self.score[comb]["coint"] = c_pvalue
            self.score[comb]["stationary"] = s_pvalue
            self.score[comb]["mean_reversion"] = hurst



class ScoreCandidates:
    def __init__(self, hurst, adf, coint, score_dict=[]):
        s = hurst+adf+coint
        self.weight_hurst = hurst/s
        self.weight_adf = adf/s
        self.weight_coint = coint/s

        self.score_dict = score_dict

    def get_top_candidates(self):
        scorings = {}
        for comb in self.score_dict.keys():
            c, s, mr = self.score_dict[comb]["coint"], self.score_dict[comb]["stationary"], self.score_dict[comb]["mean_reversion"]
            score_dict = self.weight_coint*c + self.weight_hurst*s + self.weight_adf*mr
            scorings[comb] = score_dict
        return sorted(scorings, key=lambda x: scorings[x])
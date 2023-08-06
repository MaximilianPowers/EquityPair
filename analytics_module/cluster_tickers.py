import numpy as np
from collections import defaultdict
from minisom import MiniSom
from data_loader.get_data import GetStockData
from tslearn.barycenters import dtw_barycenter_averaging
import plotly.graph_objects as go
from tqdm import tqdm

class ClusterTickers:
    def __init__(self, tickers, method, start_date, end_date):
        """
        Class that automatically identifies candidates for pair trading based on a pool
        of ticks and a given method in ["Random", "Sector", "Industry", "SOM"].

        Parameters
        ----------
        tickers : list
            List of tickers to consider.
        method : str
            Method to use for candidate identification.
        """
        self.tickers = tickers
        self.method = method
        self.g = GetStockData()

        self.som_x = None
        self.som_y = None
        self.win_map = None

        self.clusters = None
        self.start_date, self.end_date = start_date, end_date

        print("Collating data...")
        if method != 'Random':
            df = self.g.collate_dataset(self.tickers, self.start_date, self.end_date).pivot(columns='ticker', values='close')
            threshold = 0.2
            df = df.dropna(thresh=len(df) * (1 - threshold), axis=1)

            # Step 2: Remove rows with more than 5 consecutive NaNs
            drop_window = 5
            consecutive_nans = df.isna().rolling(window=drop_window+1, min_periods=drop_window+1).sum().max(axis=1)
            rows_to_remove = consecutive_nans[consecutive_nans >= drop_window+1].index
            df = df.drop(rows_to_remove)

            # Step 3: Interpolate missing values with implicit variance
            # Using 'polynomial' interpolation as an example; you can choose other methods
            df = df.interpolate(method='polynomial', order=2)
            df = df.fillna(method='ffill')
            df = df.fillna(method='bfill')

            self.df = df.drop_duplicates()
            self.df_plot = (self.df - self.df.mean())/self.df.std()
        print("Data collated.")

    def set_dates(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def set_method(self, method):
        self.method = method

    def get_candidates(self):
        """
        Get a list of candidate pairs.
     
        Parameters
        ----------
        self.start_date : str 
            Start date, only if using SOM method.
        self.end_date : str 
            End date, only if using SOM method.
        Returns
        -------
        list
            List of candidate pairs.
        """
        if self.method == "Random":
            return self.get_random_pairs()
        elif self.method == "Sector":
            return self.get_sector_pairs()
        elif self.method == "Industry":
            return self.get_industry_pairs()
        elif self.method == "SOM":
            return self.get_som_pairs()
        else:
            raise Exception("Invalid method.")
        
    def get_random_pairs(self, size=0.001):
        """
        Get random pairs set at 0.1 % of the total pool of tickers.

        Returns
        -------
        list
            List of candidate pairs.
        """
        self.clusters = None
        return [(self.tickers[i], self.tickers[j]) for i in range(len(self.tickers)) for j in range(i+1, len(self.tickers)) if np.random.rand() < size]
    
    def get_sector_pairs(self):
        """
        Get pairs from the same sector.

        Returns
        -------
        list
            List of candidate pairs.
        """
        store_dict = defaultdict(list)
        for ticker in self.tickers:
            sector = self.g.get_ticker_field_info(ticker, "sector")
            store_dict[sector].append(ticker)
        store_dict = self.filter_dict(store_dict)

        self.clusters = store_dict

        return [(store_dict[sector][i], store_dict[sector][j]) for sector in store_dict for i in range(len(store_dict[sector])) for j in range(i+1, len(store_dict[sector]))]
    
    def get_industry_pairs(self):
        """
        Get pairs from the same industry.

        Returns
        -------
        list
            List of candidate pairs.
        """
        store_dict = defaultdict(list)
        for ticker in self.tickers:
            industry = self.g.get_ticker_field_info(ticker, "industry")
            store_dict[industry].append(ticker)
        store_dict = self.filter_dict(store_dict)

        self.clusters = store_dict

        return [(store_dict[industry][i], store_dict[industry][j]) for industry in store_dict for i in range(len(store_dict[industry])) for j in range(i+1, len(store_dict[industry]))]
    
    def get_som_pairs(self):
        """
        Get pairs from the same self-organising map cluster. We set the number of clusters as the log of the number of data points (around 7).

        Returns
        -------
        list
            List of candidate pairs.
        """
        
        df = self.df.copy()
        normalized_df = (df - df.mean()) / df.std()

        X_ = normalized_df.values.T
        som_x, som_y = max(int(np.sqrt(np.sqrt(len(X_))))-1, 3), max(int(np.sqrt(np.sqrt(len(X_))))-1, 3)
        som = MiniSom(som_x, som_y, X_.shape[1], sigma=.3, learning_rate=0.1, 
                      neighborhood_function='gaussian', random_seed=10)
        som.pca_weights_init(X_)
        print("Training...")
        som.train_batch(X_, 50000, verbose=True)  # random training
        print("\n...ready!")

        store_dict = defaultdict(list)
        for idx, column in enumerate(normalized_df.columns):
            winner_node = som.winner(X_[idx])
            store_dict["Cluster " + str(winner_node[0]*som_y+winner_node[1]+1)].append(column)
        store_dict = self.filter_dict(store_dict)
        self.som_x = som_x
        self.som_y = som_y
        self.win_map = som.win_map(X_)
        self.clusters = store_dict
        print("Clusters identified.")
        return [(store_dict[cluster][i], store_dict[cluster][j]) for cluster in store_dict for i in range(len(store_dict[cluster])) for j in range(i+1, len(store_dict[cluster]))]
        
    def plot_som_clusters(self, method):
        fig = go.Figure()
        for x in range(self.som_x):
            for y in range(self.som_y):
                cluster = (x, y)
                if cluster in self.win_map.keys():
                    for series in self.win_map[cluster]:
                        fig.add_trace(go.Scatter(y=series, line=dict(color='gray', width=0.5)))
                    fig.add_trace(go.Scatter(y=method(np.vstack(self.win_map[cluster]), axis=0), line=dict(color='red'), showlegend=False))
        fig.update_layout(title='Clusters')
        return fig
    
    
    def plot_clusters(self, method, cluster):
        fig = go.Figure()
        df = self.df_plot.copy()
        columns = [series for series in self.clusters[cluster] if series in df.columns]
        showlegend = False
        for series in columns:
            fig.add_trace(go.Scatter(y=df[series].values, name=series, line=dict(color='gray', width=0.5), showlegend=showlegend))
        fig.add_trace(go.Scatter(y=method(df[columns].values.T).squeeze(), line=dict(color='red')))
        return fig

    
    
    def plot_som_bar(self):
        cluster_c = []
        cluster_n = []
        for x in range(self.som_x):
            for y in range(self.som_y):
                cluster = (x, y)
                if cluster in self.win_map.keys():
                    cluster_c.append(len(self.win_map[cluster]))
                else:
                    cluster_c.append(0)
                cluster_number = x * self.som_y + y + 1
                cluster_n.append(f"Cluster {cluster_number}")

        fig = go.Figure(data=[go.Bar(x=cluster_n, y=cluster_c)])
        fig.update_layout(title="Cluster Distribution for SOM")
        return fig
    
    
    def plot_time_series_clusters(self, avg_method, cluster):
        if avg_method not in ["Barycenters", "Mean"]:
            raise Exception("Averaging method not available")
        if self.method == "Random":
            raise Exception("The method you have chosen doesn't have clusters.")
        if cluster is None:
            raise Exception("We require a cluster to plot")

        if avg_method == "Barycenters":
            return self.plot_clusters(dtw_barycenter_averaging, cluster)
        elif avg_method == "Mean":
            return self.plot_clusters(self.average_axis_0, cluster)
        
            
    def plot_bar(self):
        if self.clusters is None:
            raise Exception("Please run get_candidates first.")
        if self.method in ["Random"]:
            raise Exception("The method you have chosen doesn't have clusters.")

        fig = go.Figure()
        res = {}
        for cluster, val in self.clusters.items():
            if cluster is None:
                cluster = "None"
            res[cluster] = len(val)
        
        if None in res.keys():
            res["None"] = res[None]
            del res[None]

        keys = list(res.keys())
        values = list(res.values())
        fig.add_trace(go.Bar(x=keys, y=values))
        fig.update_layout(title="Cluster Distribution")

        return fig
    
    @staticmethod
    def filter_dict(store_dict):
        """
        Remove keys with only one or no entries.
        """
        remove_keys = []
        for key in store_dict.keys():
            if len(store_dict[key]) < 2:
                remove_keys.append(key)
        if len(remove_keys) > 0:
            for key in remove_keys:
                del store_dict[key]

        if None in store_dict.keys():
            store_dict["None"] = store_dict[None]
            del store_dict[None]

        return store_dict
    
    @staticmethod
    def average_axis_0(x):
        return np.average(x, axis=0)
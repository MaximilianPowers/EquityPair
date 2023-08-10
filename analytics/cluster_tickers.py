import numpy as np
from minisom import MiniSom

from data_loader.singleton import get_data_fetcher 
import plotly.graph_objects as go

from collections import defaultdict
from tslearn.barycenters import dtw_barycenter_averaging

data_fetcher = get_data_fetcher()

class ClusterTickers:
    def __init__(self, tickers, method, start_date, end_date, serialise=False):
        """
        Class that automatically identifies candidates for pair trading based on a pool
        of ticks and a given method in ["Sector", "Industry", "SOM", "Market Cap"].

        Parameters
        ----------
        tickers : list
            List of tickers to consider.
        method : str
            Method to use for candidate identification.
        """
        self.tickers = tickers
        self.method = method

        self.som_x = None
        self.som_y = None
        self.win_map = None

        self.clusters = None
        self.start_date, self.end_date = start_date, end_date
        if not serialise:
            print("Collating data...")
            
            df = data_fetcher.collate_dataset(self.tickers, self.start_date, self.end_date).pivot(columns='ticker', values='close')
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

    def _serialise(self, df):
        """
        Avoid repeating data loading when class copying for group by
        on bar plot.
        """
        self.df = df
        self.df_plot = (self.df - self.df.mean())/self.df.std()

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
        if self.method == "Sector":
            return self.get_sector_pairs()
        elif self.method == "Industry":
            return self.get_industry_pairs()
        elif self.method == "SOM":
            return self.get_som_pairs()
        elif self.method == "Market Cap":
            return self.get_market_cap_pairs()
        else:
            raise Exception("Invalid method.")
        
    def get_market_cap_pairs(self):
        """
        Using quantiles of marketcaps, break the tickers into
        10 equal sized buckets and pair them up.
        """
        store_dict = defaultdict(list)
        market_caps = {}
        for ticker in self.tickers:
            market_cap = data_fetcher.get_ticker_field_info(ticker, "marketCap")
            if market_cap is None:
                market_caps[ticker] = 0
                continue

            market_caps[ticker] = market_cap
        sorted_items = sorted(market_caps.items(), key=lambda x: x[1])
        buckets = [sorted_items[i::10] for i in range(10)]
        store_dict = {f'Size {i + 1}': [item[0] for item in bucket] for i, bucket in enumerate(buckets)}
        store_dict = self.filter_dict(store_dict)

        self.clusters = store_dict

        return [(store_dict[market_cap][i], store_dict[market_cap][j]) for market_cap in store_dict for i in range(len(store_dict[market_cap])) for j in range(i+1, len(store_dict[market_cap]))]
    
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
            sector = data_fetcher.get_ticker_field_info(ticker, "sector")
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
            industry = data_fetcher.get_ticker_field_info(ticker, "industry")
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
        fig.add_trace(go.Scatter(y=method(df[columns].values.T).squeeze(), line=dict(color='red'), name="Average"))
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
        if cluster is None:
            raise Exception("We require a cluster to plot")

        if avg_method == "Barycenters":
            return self.plot_clusters(dtw_barycenter_averaging, cluster)
        elif avg_method == "Mean":
            return self.plot_clusters(self.average_axis_0, cluster)
        
            
    def plot_bar(self, cluster_2=None):
        if self.clusters is None:
            raise Exception("Please run get_candidates first.")
        if cluster_2 is not None:
            fig = go.Figure()
            a = self.clusters
            b = cluster_2
            # Calculate the counts for each segment in the bars
            a_keys = list(a.keys())
            b_values = []
            
            total_values = [sum(len(b[key]) for key in b.keys() if ticker in b[key]) for tickers in a.values() for ticker in tickers]

            # Sort keys and values by total_values in descending order
            sorted_keys = [key for _, key in sorted(zip(total_values, a.keys()))]
            
            # Create a mapping of tickers to their corresponding keys in b
            ticker_to_b_key = {ticker: key for key, tickers in b.items() for ticker in tickers}
            
            # Calculate the counts for each segment in the bars
            a_keys = list(a.keys())
            b_values = {key: [0] * len(a_keys) for key in b.keys()}
            for i, cluster_key in enumerate(a_keys):
                for ticker in a[cluster_key]:
                    b_cluster_key = ticker_to_b_key[ticker]
                    b_values[b_cluster_key][i] += 1
            
            # Sort clusters by total size
            sorted_clusters = sorted(a_keys, key=lambda cluster: -sum(b_values[key][i] for key in b.keys()))
            
            # Add the traces for each segment
            for b_cluster_key, values in b_values.items():
                sorted_values = [values[a_keys.index(cluster)] for cluster in sorted_clusters]
                fig.add_trace(go.Bar(x=sorted_clusters, y=sorted_values, name=f'{b_cluster_key}',
                                     hovertemplate=f'<b>Cluster:</b> %{{x}}<br><b>Value:</b> %{{y}}'))
            
            # Update layout
            fig.update_layout(
                barmode='stack',
                legend=dict(x=0.999, y=.9), # Adjust the x value to move the legend inside the plot area
            )
            if self.method == "Industry":
                fig.update_layout(
                    xaxis=dict(showticklabels=False)
                )
            return fig
        else:
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
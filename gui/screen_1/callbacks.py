# type: ignore

from dash.dependencies import Input, Output, State
from dash import html, dash_table
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from analytics.regression import KalmanRegression, OLSRegression, CointegrationTest
from analytics.cluster_tickers import ClusterTickers
from analytics.identify_tickers import IdentifyCandidates, ScoreCandidates

from data_loader.singleton import get_data_fetcher, get_misc_connect
from gui.utils import date_handler
from utils.utils import safe_round

import numpy as np
import pandas as pd

data_fetcher = get_data_fetcher()
misc_connect = get_misc_connect()

global cluster_method

def register_analytics_callbacks(app):
    global cluster_method
    cluster_method = None
    @app.callback(
        Output('ticker-dropdown-2', 'value'),
        Input('ticker-dropdown-2', 'value')
    )
    def limit_dropdown_selection(tickers):
        if len(tickers) > 2:
            return tickers[-2:]
        return tickers


    @app.callback(
        Output('time-series-plot-1', 'figure'),
        [Input('submit-button-1', 'n_clicks')],
        [State('ticker-dropdown-1', 'value'),
         State('my-date-picker-range-1', 'start_date'),
         State('my-date-picker-range-1', 'end_date')]
    )
    def update_time_series_plot(n, tickers, s_date, e_date):
        
        start_date = date_handler(s_date)
        end_date = date_handler(e_date)
        # Fetch data
        data_fetcher.set_dates(start_date, end_date)
        fig = go.Figure()

        for ticker in tickers:
            df = data_fetcher.get_data(ticker)
            ts = df['close'].values

            # Create figure
            fig.add_trace(go.Scatter(x=df.index, y=ts, mode='lines', name=ticker))
        fig.update_layout(xaxis_title="Date", yaxis_title="Price", margin=dict(l=0, r=0, t=0, b=0))

        return fig



    @app.callback(
        Output('dependent-dropdown', 'options'),
        [Input('submit-button-3', 'n_clicks'),
        Input('automatic-dropdown-1', 'value'),
        Input('my-date-picker-range-3', 'start_date'),
        Input('my-date-picker-range-3', 'end_date')],
    )
    def cluster_tickers(n, method, s_date, e_date):
        global cluster_method  # Declare cluster_method as global
        if n is None:
            return []
        start_date = date_handler(s_date)
        end_date = date_handler(e_date)
        data_fetcher.set_dates(start_date, end_date)
        tickers = data_fetcher.get_ticker_names()
        # To repeat loading in data repetitively
        if cluster_method is None:
            cluster_method = ClusterTickers(tickers, method, start_date, end_date)
        else:
            if cluster_method.start_date != start_date or cluster_method.end_date != end_date:
                cluster_method = ClusterTickers(tickers, method, start_date, end_date)
            cluster_method.clusters = None
            cluster_method.set_dates(start_date, end_date)
            cluster_method.set_method(method)
        cluster_method.get_candidates()
        # Sorting the dictionary by the length of the lists
        sorted_clusters = {k: v for k, v in sorted(cluster_method.clusters.items(), key=lambda item: len(item[1]), reverse=True)}
        misc_connect.post_clustering_results(method, start_date, end_date, sorted_clusters)
        # Creating the sorted_list by iterating through the sorted keys
        sorted_list = [{"label": key, "value": key, "search": key} for key in sorted_clusters.keys()]
        return sorted_list

    @app.callback(
        [Output('cluster-plot-1', 'figure'),
         Output('bar-plot-1', 'figure')],
        [Input('submit-button-4', 'n_clicks'), 
         Input('average-method-choice', 'value'),
         Input('dependent-dropdown', 'value'),
         Input('groupby-dropdown', 'value')],
    )
    def plot_clusters(n, avg_method, cluster, groupby):
        global cluster_method
        if cluster_method is not None and cluster is not None and n is not None and n != 0 and cluster_method.clusters is not None:
            fig_1 = cluster_method.plot_time_series_clusters(avg_method, cluster)
            if groupby == 'None':
                fig_2 = cluster_method.plot_bar()
            elif groupby == 'sector':
                cluster_method_copy = ClusterTickers(cluster_method.tickers, "Sector", cluster_method.start_date, cluster_method.end_date, serialise=True)
                cluster_method_copy._serialise(cluster_method.df)
                cluster_method_copy.get_candidates()
                fig_2 = cluster_method.plot_bar(cluster_method_copy.clusters)
            elif groupby == 'market_cap':
                cluster_method_copy = ClusterTickers(cluster_method.tickers, "Market Cap", cluster_method.start_date, cluster_method.end_date, serialise=True)
                cluster_method_copy._serialise(cluster_method.df)
                cluster_method_copy.get_candidates()
                fig_2 = cluster_method.plot_bar(cluster_method_copy.clusters)

            
            fig_1.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            fig_2.update_layout(margin=dict(l=0, r=0, t=0, b=0))

            return fig_1, fig_2    
        else:
            fig_1 = go.Figure()
            fig_2 = go.Figure()
            fig_1.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            fig_2.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            return fig_1, fig_2

    @app.callback(
            Output('cluster-dropdown', 'options'),
            [Input('submit-button-6', 'n_clicks')]
    )
    def update_cluster_dropdown(n):
        if n is not None and n != 0:
            options = []
            dict_ = misc_connect.get_all_clustering_results()
            for document in dict_:
                method = document['method']
                start_date = document['start_date']
                end_date = document['end_date']
                label = f'{method}:{start_date}:{end_date}'
                options.append({'label': label, 'value': label, 'search': label})
            return options
        else:
            return []
        
    @app.callback(
            Output('cluster-selection', 'options'),
            [Input('cluster-dropdown', 'value'),
             Input('submit-button-6', 'n_clicks')]
    )
    def update_cluster_selection(cluster, n):
        if n is not None and n != 0:
            if cluster is not None:
                method, start_date, end_date = cluster.split(':')
                cursor = misc_connect.get_clustering_results(method, start_date, end_date)
                clusters = list(cursor)
                return [{"label": key, "value": key, "search": key} for key in clusters]
            else:
                return []
        else:
            return []

    @app.callback(
        Output('numerical-data-1', 'children'),
        [Input('submit-button-1', 'n_clicks')],
        [State('ticker-dropdown-1', 'value')]
    )
    def update_numerical_data(n, tickers):
        if n is None or n == 0 or tickers is None or len(tickers) == 0:
            return dash_table.DataTable(
            data=None,
            columns=[{'name': 'Ticker', 'id': 'Ticker'},
                     {'name': 'Market Cap/B', 'id': 'Market Cap/B'},
                     {'name': 'Sector', 'id': 'Sector'},
                     {'name': 'Industry', 'id': 'Industry'},
                     {'name': 'Beta', 'id': 'Beta'}],
            style_cell={
                'textAlign': 'left',
                'overflow': 'hidden', # this line will keep the text from spilling out of the cell
                'textOverflow': 'ellipsis', # this line will truncate the text with an ellipsis
                'maxWidth': 0, # this line will allow the text to break across lines
                'whiteSpace': 'normal' # this line will allow the text to break across lines
                
            },
            style_data_conditional=[{'if': {'column_id': 'column 1'}, 'textOverflow': 'ellipsis'}],
            style_table={
                'overflowX': 'scroll', # this line will make the table horizontally scrollable
            },
            css=[{
                'selector': '.dash-cell div.dash-cell-value',
                'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
            }]
            )

        data = []
        n = max(0, -7+len(tickers))
        for ticker in tickers[n:]:
            sector = data_fetcher.get_ticker_field_info(ticker, field='sector')
            industry = data_fetcher.get_ticker_field_info(ticker, field='industry')
            marketCap = data_fetcher.get_ticker_field_info(ticker, field='marketCap')
            beta = data_fetcher.get_ticker_field_info(ticker, field='beta')


            marketCap = safe_round(marketCap/1_000_000_000,2) if marketCap is not None else 0
            data.append({'Ticker': ticker, 'Market Cap/B': marketCap, 'Sector': sector, 'Industry': industry, 'Beta': beta})

        # Create a DataTable
        table = dash_table.DataTable(
            data=data,
            columns=[{'name': 'Ticker', 'id': 'Ticker'},
                     {'name': 'Market Cap/B', 'id': 'Market Cap/B'},
                     {'name': 'Sector', 'id': 'Sector'},
                     {'name': 'Industry', 'id': 'Industry'},
                     {'name': 'Beta', 'id': 'Beta'}],
            style_cell={
                'textAlign': 'left',
                'overflow': 'hidden', # this line will keep the text from spilling out of the cell
                'textOverflow': 'ellipsis', # this line will truncate the text with an ellipsis
                'maxWidth': 0, # this line will allow the text to break across lines
                'whiteSpace': 'normal' # this line will allow the text to break across lines
                
            },
            style_data_conditional=[{'if': {'column_id': 'column 1'}, 'textOverflow': 'ellipsis'}],
            style_table={
                'overflowX': 'scroll', # this line will make the table horizontally scrollable
            },
            css=[{
                'selector': '.dash-cell div.dash-cell-value',
                'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
            }]
        )

        return table
    @app.callback(
        Output('pairs-success', 'children'),
        [Input('submit-button-5', 'n_clicks')],
        [State('cluster-dropdown', 'value'),
         State('cluster-selection', 'value')
         ]
    )
    def identify_pairs(n, clusters, cluster):
        if n is not None and n != 0:
            if cluster is not None:
                method, start_date, end_date = clusters.split(':')
                tickers = list(misc_connect.get_cluster(method, cluster, start_date, end_date))
                ticker_pairs = [(tickers[i], tickers[j]) for i in range(len(tickers)) for j in range(i+1, len(tickers))]
                df = data_fetcher.collate_dataset(tickers, start_date, end_date)
                df = df.pivot(columns='ticker', values='close')

                candidates = IdentifyCandidates(ticker_pairs, df, max_lag=None)
                candidates.iterate_tickers()
                misc_connect.post_pairs_results(method, cluster, start_date, end_date, candidates.score)
                return "Done!"
            else:
                return ""
        else:
            return ""
        
    @app.callback(
        [Output('loading-bar', 'value'),
         Output('time-taken', 'children'),
         Output('time-remaining', 'children')],
        [Input('submit-button-5', 'n_clicks')],
    )    
    def update_progress_bar(n_clicks):
        progress = 50  # Example value
        time_taken = 10  # Example value in seconds
        time_remaining = 20  # Example value in seconds

        return progress, f'Time taken: {time_taken}s', f'Time remaining: {time_remaining}s'
    
    @app.callback(
            Output("pairs-dropdown", "options"),
            [Input("submit-button-8", "n_clicks")]
    )
    def get_all_pair_runs(n_clicks):
        res = list(misc_connect.get_all_pairs_results())
        if len(res) > 0:
            options = []
            for dict_ in res:
                cluster = dict_['chosen_cluster']
                method = dict_['method']
                end_date = dict_['end_date']
                start_date = dict_['start_date']

                pair_name = method + ':' + cluster + ':' + start_date + ':' + end_date
                options.append({'label': pair_name, "value": pair_name, "search": pair_name})
            return options
        else:
            return []
        
    @app.callback(
        [Output('pair-data-1', 'children'),
         Output('pair-plot-1', 'figure')],
        [Input('submit-button-7', 'n_clicks'),
         Input('pairs-dropdown', 'value')],
         [
             State('slider-K', 'value'),
             State('slider-hurst', 'value'),
             State('slider-stat', 'value'),
             State('slider-coint', 'value'),
          ]
    )
    def get_pairs_table(n, str_, K, hurst, stat, coint):
        if str_ is None:
            fig = go.Figure()
            fig.update_layout(xaxis_title="Date", yaxis_title="Price", margin=dict(l=0, r=0, t=36, b=0))
            return "", fig
        method, cluster, start_date, end_date = str_.split(':')
        cursor = misc_connect.get_pairs_results(method, cluster, start_date, end_date)
        res = dict(cursor)
        S = ScoreCandidates(hurst, stat, coint, res)

        final_table = []
        tickers = S.get_top_candidates()
        for key in tickers:
            ticker_1, ticker_2 = key.split(':')
            t1_beta = safe_round(data_fetcher.get_ticker_field_info(ticker_1, 'beta'), 2)
            t1_market_cap = safe_round(data_fetcher.get_ticker_field_info(ticker_1, 'marketCap'))/1_000_000_000
            t2_beta = safe_round(data_fetcher.get_ticker_field_info(ticker_2, 'beta'), 2)
            t2_market_cap = safe_round(data_fetcher.get_ticker_field_info(ticker_2, 'marketCap'))/1_000_000_000
            coint_val = safe_round(res[key]['coint'], 3)
            stat_val = safe_round(res[key]['stationary'], 3)
            hurst_val = safe_round(res[key]['mean_reversion'], 3)

            s_ = hurst+stat+coint
            total = safe_round((coint*coint_val + hurst*hurst_val + stat*stat_val)/s_, 3)
            final_table.append({
                    'Ticker 1': ticker_1,
                    'Ticker 2': ticker_2,
                    '\u03B2 1': t1_beta,
                    '\u03B2 2': t2_beta,
                    'Market Cap 1/B': t1_market_cap,
                    'Market Cap 2/B': t2_market_cap,
                    'Coint': coint_val,
                    'Hurst': hurst_val,
                    'Stationary': stat_val,
                    'Total': total
                })
            

        df_fin = pd.DataFrame(final_table)
        # Combine beta and market cap values, and drop duplicates
        beta_values = pd.Series(df_fin['\u03B2 1'].tolist() + df_fin['\u03B2 2'].tolist()).drop_duplicates().sort_values()
        market_cap_values = pd.Series(df_fin['Market Cap 1/B'].tolist() + df_fin['Market Cap 2/B'].tolist()).drop_duplicates().sort_values()

        # Define quantiles for the columns
        quantiles = {
            'Hurst': np.linspace(0, 1, 11),
            'Stationary': np.linspace(0, 1, 11),
            'Coint': np.linspace(0, 1, 11),
            'Total': np.linspace(0, 1, 11),
            '\u03B2': np.linspace(beta_values.min(), beta_values.max(), 11),
            'Market Cap': np.linspace(market_cap_values.min(), market_cap_values.max(), 11),
        }

        # Define colors for the quantiles
        colors = list(reversed(['#a6d96a', '#b8e081', '#cde996', '#e1f2ac', '#f5fac2', '#f9f8a2', '#fde480', '#fbcf5e', '#f9b93d', '#f79e1b']))


        # Create style_data_conditional
        style_data_conditional = []
        columns_to_style = ['\u03B2 1', '\u03B2 2', 'Market Cap 1/B', 'Market Cap 2/B', 'Coint', 'Hurst', 'Stationary', 'Total']
        for column in columns_to_style:
            if column in ['\u03B2 1', '\u03B2 2']:
                quants = quantiles['\u03B2']
            elif column in ['Market Cap 1/B', 'Market Cap 2/B']:
                quants = quantiles['Market Cap']
            else:
                quants = quantiles[column]
            for i in range(10):
                condition = {
                    "if": {
                        "filter_query": f"{{{column}}} >= {quants[i]} && {{{column}}} < {quants[i+1]}",
                        "column_id": column
                    },
                    "backgroundColor": colors[i] if column in ['\u03B2 1', '\u03B2 2', 'Market Cap 1/B', 'Market Cap 2/B'] else colors[9-i]
                }
                style_data_conditional.append(condition)
        df_table = pd.DataFrame(final_table[:K])
        table = dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df_table.columns],
            data=df_table.to_dict('records'),
            style_cell={'textAlign': 'left'},
            style_data_conditional=style_data_conditional
        )
        nbins = 10
        # Create a 3x2 grid of subplots
        fig = make_subplots(rows=3, cols=2, subplot_titles=['\u03B2', 'Market Cap', 'Cointegration', 'Hurst', 'Stationary', 'Total'])

        # Add the histogram for beta
        fig.add_trace(
            go.Histogram(x=pd.concat([df_fin['\u03B2 1'], df_fin['\u03B2 2']], axis=0), nbinsx=nbins, name='Beta'),
            row=1, col=1
        )

        # Add the histogram for market cap
        fig.add_trace(
            go.Histogram(x=pd.concat([df_fin['Market Cap 1/B'], df_fin['Market Cap 2/B']], axis=0), nbinsx=nbins, name='Market Cap'),
            row=1, col=2
        )

        # Add the histogram for cointegration
        fig.add_trace(
            go.Histogram(x=df_fin['Coint'], nbinsx=nbins, name='Cointegration'),
            row=2, col=1
        )

        # Add the histogram for Hurst
        fig.add_trace(
            go.Histogram(x=df_fin['Hurst'], nbinsx=nbins, name='Hurst'),
            row=2, col=2
        )

        # Add the histogram for stationary
        fig.add_trace(
            go.Histogram(x=df_fin['Stationary'], nbinsx=nbins, name='Stationary'),
            row=3, col=1
        )

        # Add the histogram for Total
        fig.add_trace(
            go.Histogram(x=df_fin['Total'], nbinsx=nbins, name='Total'),
            row=3, col=2
        )

        # Update layout
        fig.update_layout(title='Histograms', showlegend=False)
        fig.update_layout(margin=dict(l=0, r=0, t=36, b=0))

        return table, fig
    
    @app.callback(
        [Output('time-series-plot-3', 'figure'),
        Output('insert-res', 'children')],
        [Input('submit-button-2', 'n_clicks')],
        [State('ticker-dropdown-2', 'value'),
        State('my-date-picker-range-2', 'start_date'),
        State('my-date-picker-range-2', 'end_date')]
    )
    def update_hedging_ratio_plot(n, tickers, s_date, e_date):
        start_date = date_handler(s_date)
        end_date = date_handler(e_date)
        # Parse tickers
        if len(tickers) < 2:
            fig = go.Figure()
            fig.update_layout(xaxis_title="Date", yaxis_title="Price", margin=dict(l=0, r=0, t=36, b=0))
            return fig
        ticker1, ticker2 = tickers[-2:]

        # Fetch data
        df = data_fetcher.collate_dataset([ticker1, ticker2], start_date, end_date)
        df = df.pivot(columns='ticker', values='close')
        df = df.dropna()
        # Compute OLS hedging ratio
        ols = OLSRegression(df[ticker2], df[ticker1])   
        ols.run()
        ols_hedging_ratio = ols.cur_beta
        ols_hedging_const = ols.cur_alpha

        # Compute Kalman Filter hedging ratio
        kalman = KalmanRegression(df[ticker2], df[ticker1], maxlen=2)
        kalman.run()
        kf_hedging_ratio = kalman.cur_beta
        kf_hedging_const = kalman.cur_alpha
        # Compute cointegration test
        coint = CointegrationTest(df[ticker1], df[ticker2])
        coint.run()
        adf_coef = coint.cur_adf

        # Create figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df[ticker2] * ols_hedging_ratio + ols_hedging_const, mode='lines', name=f"OLS {ticker1}"))
        fig.add_trace(go.Scatter(x=df.index, y=df[ticker2] * kf_hedging_ratio + kf_hedging_const, mode='lines', name=f"KF {ticker1}"))
        fig.add_trace(go.Scatter(x=df.index, y=df[ticker1], mode='lines', name=ticker1))
        fig.add_trace(go.Scatter(x=df.index, y=df[ticker2], mode='lines', name=ticker2))

        fig.update_layout(xaxis_title="Date", yaxis_title="Price", margin=dict(l=0, r=0, t=36, b=0))

        # Create information text
        info_text = f"OLS: {ols_hedging_ratio:.3f} | Kalman: {kf_hedging_ratio:.3f} | ADF: {adf_coef:.3f}"
        div = html.H3(
                        children = info_text,
                        style = {"fontWeight": "bold", "width": "100%"}
                    )
        # Return figure and markdown in a Div
        return fig, div

    @app.callback(
        Output('time-series-plot-2', 'figure'),
        [Input('submit-button-2', 'n_clicks')],
        [State('ticker-dropdown-2', 'value'),
        State('my-date-picker-range-2', 'start_date'),
        State('my-date-picker-range-2', 'end_date')]
    )
    def update_time_series_plot_2(n, tickers, s_date, e_date):
        start_date = date_handler(s_date)
        end_date = date_handler(e_date)

        if len(tickers) < 2:
            fig = go.Figure()
            fig.update_layout(xaxis_title="Date", yaxis_title="Price", margin=dict(l=0, r=0, t=36, b=0))
            return fig

        ticker1, ticker2 = tickers[-2:]
        # Fetch data
        df = data_fetcher.collate_dataset([ticker1, ticker2], start_date, end_date)
        df = df.pivot(columns='ticker', values='close')
        df['baseline'] = df[ticker1] - df[ticker2]
        mu, var = df['baseline'].mean(), df['baseline'].var()
        df['baseline'] = (df['baseline'] - mu) / np.sqrt(var)
        const = np.ones_like(df['baseline'].values)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['baseline'], mode='lines', name=f"{ticker1} - {ticker2}"))
        fig.add_trace(go.Scatter(x=df.index, y=const, mode='lines', line=dict(dash='dashdot', color="orange"), name=u"\u00B1 \u03C3"))
        fig.add_trace(go.Scatter(x=df.index, y=-const, mode='lines', line=dict(dash='dashdot', color="orange"), showlegend=False))
        fig.add_trace(go.Scatter(x=df.index, y=2*const, mode='lines', line=dict(dash='dashdot', color="red"), name=u"\u00B1 2\u03C3"))
        fig.add_trace(go.Scatter(x=df.index, y=-2*const, mode='lines', line=dict(dash='dashdot', color="red"), showlegend=False))

        fig.update_layout(xaxis_title="Date", yaxis_title="Price", margin=dict(l=0, r=0, t=36, b=0))

        return fig
    
    @app.callback(
    Output('slider-coint-value', 'children'),
        Input('slider-coint', 'value')
    )
    def update_coint_value(value):
        return f'Coint: {value:.2f}' 
    
    @app.callback(
    Output('slider-hurst-value', 'children'),
        Input('slider-hurst', 'value')
    )
    def update_hurst_value(value):
        return f'Hurst: {value:.2f}' 

    @app.callback(
    Output('slider-stat-value', 'children'),
        Input('slider-stat', 'value')
    )
    def update_stat_value(value):
        return f'ADF: {value:.2f}' 
    
    @app.callback(
    Output('slider-K-value', 'children'),
        Input('slider-K', 'value')
    )
    def update_Kvalue(value):
        return f'Top-K: {value:.2f}' 
    
    
    
    
    
    
        
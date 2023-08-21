# type: ignore
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dcc, dash_table
from dash.exceptions import PreventUpdate

import plotly.graph_objects as go

from gui.utils import str_to_date, date_handler, create_dropdown
from finance.online_strategy import OnlineRegressionStrategy
from finance.post_trade_analysis import PostTradeMetrics
from data_loader.singleton import get_misc_connect

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

misc_connect = get_misc_connect()

global uuids
def register_trade_callbacks(app, names):
    global uuids
    uuids = None
    @app.callback(
        [Output('trade-results-1', 'figure'),
         Output('trade-results-2', 'figure'),
         Output('trade-results-3', 'figure'),
         Output('trade-results-4', 'figure')
         ],
         [
             Input('run-trade-button', 'n_clicks'),
             Input('trade-ticker-dropdown-1', 'value'),
             Input('choose-method-dropdown', 'value'),
             Input('slider-sigma-buy', 'value'),
             Input('slider-sigma-sell-low', 'value'),
             Input('slider-sigma-sell-high', 'value'),
             Input('slider-maxlen', 'value'),
             Input('slider-adf-window', 'value'),
             Input('slider-adf-pvalue', 'value'),
          ],
          [
              State('train-date-1', "start_date"),
              State('train-date-1', "end_date"),
              State('trade-date-1', "start_date"),
              State('trade-date-1', "end_date")
          ]
    )
    def single_pair_trade_plot(n, tickers, method, sigma_buy,
                               sigma_sell_low, sigma_sell_high,
                               maxlen, adf_window, adf_pvalue, start_date_train, end_date_train,
                               start_date_trade, end_date_trade):
        if n is None or n == 0:
            fig_1 = go.Figure()
            fig_1.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            return fig_1, fig_1, fig_1, fig_1
        if tickers is None:
            fig_1 = go.Figure()
            fig_1.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            return fig_1, fig_1, fig_1, fig_1
        if len(tickers) != 2:
            fig_1 = go.Figure()
            fig_1.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            return fig_1, fig_1, fig_1, fig_1
        
        start_date_train = date_handler(start_date_train)
        end_date_train = date_handler(end_date_train)
        start_date_trade = date_handler(start_date_trade)
        end_date_trade = date_handler(end_date_trade)

        CAPITAL = 10_000_000
        ticker_1, ticker_2 = tickers
        hyperparameters = {"buy_sigma": sigma_buy, "sell_sigma_low": sigma_sell_low,
                     "sell_sigma_high": sigma_sell_high, "maxlen": maxlen, 
                     "coint_maxlen": adf_window, "adf_pvalue": adf_pvalue}
        method_name = method+"Regression"

        strategy = OnlineRegressionStrategy(method_name, CAPITAL, ticker_1, ticker_2, 
                                            start_date_train, end_date_train,
                                            start_date_trade, end_date_trade,
                                            hyperparameters, None)
        strategy.train_model()
        strategy.trade_model()
        strategy.post_trades(misc_connect)
        # Cointegration results
        dates, coint_spread, p_values = strategy.run_cointegration_test(adf_window)

        fig1 = go.Figure()
        ts1 = strategy.ts[strategy.ts["Mode"] == "Trade"][ticker_1]
        ts1.index = pd.to_datetime(ts1.index)
        ts2 = strategy.ts[strategy.ts["Mode"] == "Trade"][ticker_2]
        ts2.index = pd.to_datetime(ts2.index)
        # Add line traces for ts1 and ts2
        fig1.add_trace(go.Scatter(x=ts1.index, y=ts1.values, mode='lines', name=ticker_1, line=dict(color='orange')))
        fig1.add_trace(go.Scatter(x=ts2.index, y=ts2.values, mode='lines', name=ticker_2, line=dict(color='blue')))

        # Add trade details
        ticker_1 = strategy.ticker_1
        ticker_2 = strategy.ticker_2
        y_values_combined = np.concatenate([ts1.values, ts2.values])

        # Compute the lower and upper bounds
        y_max = y_values_combined.max()*1.1
        y_min = 0
        fig1.update_yaxes(range=[y_min, y_max])
        legend_1, legend_2 = None, None
        for key in list(strategy.portfolio.closed_trades.keys()):
            trade = strategy.portfolio.closed_trades[key]
            entry_date = pd.to_datetime(trade["entry_date"])
            exit_date = pd.to_datetime(trade["trade_exit_date"])
            pnl = trade["pnl"]

            if trade['long_ticker'] == ticker_1:
                dash_style = "dash"
                name = f"{ticker_1}/{ticker_2}"
                if legend_1 is None:
                    legend_1 = True
                fig1.add_annotation(x=exit_date, y=ts1.loc[exit_date], text=np.round(pnl, 2), showarrow=True, arrowhead=1, arrowcolor='green')

            else:
                dash_style = "dot"
                name = f"{ticker_1}/{ticker_2}"
                if legend_2 is None:
                    legend_2 = True
                fig1.add_annotation(x=exit_date, y=ts2.loc[exit_date], text=np.round(pnl, 2), showarrow=True, arrowhead=1, arrowcolor='green')



            if legend_1 or legend_2:
                fig1.add_trace(go.Scatter(
                    x=[entry_date, entry_date], 
                    y=[y_min,y_max], 
                    mode='lines', 
                    line=dict(color='green', dash=dash_style), 
                    name="Enter " + name, # Legend label 
                    yaxis='y1'))

                fig1.add_trace(go.Scatter(
                    x=[exit_date, exit_date], 
                    y=[y_min,y_max], 
                    mode='lines', 
                    line=dict(color='red', dash=dash_style), 
                    name="Exit " + name, # Legend label 
                    yaxis='y1'))
                if legend_1:
                    legend_1 = False
                if legend_2:
                    legend_2 = False
            else:
                fig1.add_trace(go.Scatter(
                    x=[entry_date, entry_date], 
                    y=[y_min,y_max], 
                    mode='lines', 
                    line=dict(color='green', dash=dash_style), 
                    name="Enter " + name, # Legend label 
                    yaxis='y1',
                    showlegend=False))

                fig1.add_trace(go.Scatter(
                    x=[exit_date, exit_date], 
                    y=[y_min,y_max], 
                    mode='lines', 
                    line=dict(color='red', dash=dash_style), 
                    name="Exit " + name, # Legend label 
                    yaxis='y1',
                    showlegend=False))

        fig1.update_layout(xaxis_title="Date", yaxis_title="Price")
        fig1.update_layout(margin=dict(l=0, r=0, t=36, b=0))
        ts1 = strategy.ts[strategy.ts["Mode"] == "Train"][ticker_1]
        ts1.index = pd.to_datetime(ts1.index)
        ts2 = strategy.ts[strategy.ts["Mode"] == "Train"][ticker_2]
        ts2.index = pd.to_datetime(ts2.index)

        # Plot portfolio value
        trades_ = strategy.portfolio.closed_trades

        exit_dates = [trades_[record]["trade_exit_date"] for record in trades_.keys()]

        pnls = [trades_[record]["pnl"] for record in trades_.keys()]

        exit_dates_normal = [trades_[record]["trade_exit_date"] for record in trades_.keys() if trades_[record]["long_ticker"] == ticker_1]
        exit_dates_swapped = [trades_[record]["trade_exit_date"] for record in trades_.keys() if trades_[record]["long_ticker"] == ticker_2]

        pnls_normal = [trades_[record]["pnl"] for record in trades_.keys() if trades_[record]["long_ticker"] == ticker_1]
        pnls_swapped = [trades_[record]["pnl"] for record in trades_.keys() if trades_[record]["long_ticker"] == ticker_2]

        # Create date range
        all_dates = pd.date_range(start=start_date_trade, end=end_date_trade, freq='D')
        # Create DataFrame
        df = pd.DataFrame(index=all_dates)
        df['PnLSwapped'] = None
        df['PnLNormal'] = None
        df['PnL'] = None

        # Fill PnL_Exit column with PnL values at exit dates
        for date, pnl in zip(exit_dates, pnls):
            df.loc[date, 'PnL'] = pnl

        # Fill PnL_Exit column with PnL values at exit dates
        for date, pnl in zip(exit_dates_normal, pnls_normal):
            df.loc[date, 'PnLNormal'] = pnl
        
        # Fill PnL_Exit column with PnL values at exit dates
        for date, pnl in zip(exit_dates_swapped, pnls_swapped):
            df.loc[date, 'PnLSwapped'] = pnl
        
        # Fill forward PnL column
        df['PnL'] = df['PnL'].fillna(0)
        df['PnLSwapped'] = df['PnLSwapped'].fillna(0)
        df['PnLNormal'] = df['PnLNormal'].fillna(0)

        # Fill with zeros between the first date and the first trade
        if len(exit_dates)>= 1:
            first_trade_date = exit_dates[0]
            df.loc[:first_trade_date, 'PnL'] = df.loc[:first_trade_date, 'PnL'].fillna(0)
        else:
            df['PnL'] = df['PnL'].fillna(0)
        if len(exit_dates_normal)>= 1:
            first_trade_date = exit_dates_normal[0]
            df.loc[:first_trade_date, 'PnLNormal'] = df.loc[:first_trade_date, 'PnLNormal'].fillna(0)
        else:
            df['PnLNormal'] = df['PnLNormal'].fillna(0)

        if len(exit_dates_swapped)>= 1:
            first_trade_date = exit_dates_swapped[0]
            df.loc[:first_trade_date, 'PnLSwapped'] = df.loc[:first_trade_date, 'PnLSwapped'].fillna(0)
        else:
            df['PnLSwapped'] = df['PnLSwapped'].fillna(0)
        # Resulting DataFrame
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x = df.index, y=df["PnL"].cumsum(), mode='lines', name=f"Profit"))
        fig2.add_trace(go.Scatter(x = df.index, y=df["PnLNormal"].cumsum(), mode='lines', line=dict(dash='dash'), name=f"Normal {ticker_1}/{ticker_2}"))
        fig2.add_trace(go.Scatter(x = df.index, y=df["PnLSwapped"].cumsum(), mode='lines', line=dict(dash='dash'), name=f"Swapped {ticker_2}/{ticker_1}"))
        fig2.update_layout(yaxis_title="Profit", xaxis_title="Time", margin=dict(l=0, r=0, t=36, b=0))
        fig2.update_layout(legend=dict(x=0,y=1,xanchor='left',yanchor='top'))


        final_total_profit = df["PnL"].cumsum().iloc[-1] 
        final_normal_profit = df["PnLNormal"].cumsum().iloc[-1] 
        final_swapped_profit = df["PnLSwapped"].cumsum().iloc[-1] 

        unique_final_profits = {
            final_total_profit: f"Total",
            final_normal_profit: f"Normal",
            final_swapped_profit: f"Swapped",
        }

        # Create annotations for each unique final profit
        annotations = []
        for profit, label in unique_final_profits.items():
            y_values = [
                final_total_profit if label == "Total" else None,
                final_normal_profit if label == f"Normal" else None,
                final_swapped_profit if label == f"Swapped" else None,
            ]
            y_values = [y for y in y_values if y is not None]
            y_pos = y_values[0]  # Position for the annotation (they are equal, so any value can be used)

            text = f"<b>{profit:.3e}</b>"

            annotations.append(
                dict(
                    x=df.index[-1], y=y_pos,
                    text=text,
                    showarrow=True, arrowhead=2, ax=-10, ay=-40,
                    font=dict(size=12)
                )
            )

        fig2.update_layout(annotations=annotations)

        res = np.array(strategy.store_res)
        ts1 = strategy.ts[strategy.ts["Mode"] == "Trade"][ticker_1]
        ts1.index = pd.to_datetime(ts1.index)
        ts2 = strategy.ts[strategy.ts["Mode"] == "Trade"][ticker_2]
        ts2.index = pd.to_datetime(ts2.index)
        ts = ts2 - ts1
        ts = ts.dropna()
        mu_ts = ts.mean()
        var_ts = ts.var()        
        ts = (ts - mu_ts) / np.sqrt(var_ts)
        # Create a Plotly figure
        fig3 = go.Figure()
        # Add line traces for each column in res
        fig3.add_trace(go.Scatter(x=ts.index, y=res[:, 0], mode='lines', name="Normal Buy"))
        fig3.add_trace(go.Scatter(x=ts.index, y=res[:, 1], mode='lines', name="Swapped Buy"))
        fig3.add_trace(go.Scatter(x=ts.index, y=res[:, 2], mode='lines', name="Normal Sell"))
        fig3.add_trace(go.Scatter(x=ts.index, y=res[:, 3], mode='lines', name="Swapped Sell"))
        fig3.add_trace(go.Scatter(x=ts.index, y=coint_spread, mode='lines', name=f"Cointegration: {adf_window}"))

        if not np.isnan(res[:, 4]).any() and not np.isnan(res[:, 5]).any():
            fig3.add_trace(go.Scatter(x=ts.index, y=res[:, 4], mode='lines', name="Normal StopLoss"))
            fig3.add_trace(go.Scatter(x=ts.index, y=res[:, 5], mode='lines', name="Swapped StopLoss"))
        fig3.add_trace(go.Scatter(x=ts.index, y=res[:, -1], mode='lines', name="Estimated Spread"))
        fig3.add_trace(go.Scatter(x=ts.index, y=ts, mode='lines', name="True Spread"))
        # Set title, x label, and legend position
        fig3.update_layout(yaxis_title="Spread", xaxis_title="Time", margin=dict(l=0, r=0, t=36, b=0))
        print('-'*50)
        print(f'For Pair Strategy: {ticker_1} / {ticker_2}')
        print(f"Training: {start_date_train} / {end_date_train}")
        print(f"Trading: {start_date_trade} / {end_date_trade}")
        print(f"Starting Capital: {strategy.portfolio.starting_capital}")
        print(f"Profit: {strategy.portfolio.pnl}")
        print(f"Trades: {len(strategy.portfolio.closed_trades)}")
        #print(f"Sharpe Ratio: {strategy.portfolio.calculate_sharpe_ratio(0.01)}")
        #print(f"Max Drawdown: {strategy.portfolio.calculate_max_drawdown()}")
        #print(f"Calmar Ratio: {strategy.portfolio.calculate_calmar_ratio()}")
        #print(f"Sortino Ratio: {strategy.portfolio.calculate_sortino_ratio(0.01, 0.01)}")

        print('-'*50)


        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=dates, y=p_values, mode='lines', name="p-value"))
        fig4.update_layout(yaxis_title="ADF p-value", xaxis_title="Time", margin=dict(l=0, r=0, t=36, b=0))
        return fig1, fig2, fig3, fig4
    




    @app.callback(
        Output('empty-div', 'children'),
        Output('uuid-storage-final', 'data'),
        Input('submit-button-trade', 'n_clicks'),
    )
    def evaluate_strategy(n):
        if n is None or n == 0:
            return "", {}
        global uuids
        
        if uuids is None:
            return "", {}
        if len(uuids) < 1:
            return "", {}
        
        for uuid in uuids:
            continue
        return "", uuids
    
    @app.callback(
        [
        Output('risk-metric-graph-1', 'figure'),
        Output('risk-metric-graph-2', 'figure'),
        Output('risk-metric-graph-3', 'figure'),
        Output('risk-metric-graph-4', 'figure'),
        Output('strategy-data-1', 'children')
        ],
        [Input('evaluate-button', 'n_clicks'),
        Input('uuid-storage-final', 'data')],
        [
        State('target-return', 'value'),
        State('risk-free-rate', 'value')]
    )
    def plot_results(n, uuids, target_rate, risk_free_rate):
        if n is None or n == 0:
            fig = go.Figure()
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            return fig, fig, fig, fig, ""
        if uuids is None:
            fig = go.Figure()
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            return fig, fig, fig, fig, ""
        if len(uuids) < 1:
            fig = go.Figure()
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            return fig, fig, fig, fig, ""
        

        res_dict = {}
        for uuid in uuids:
            strategy_data, strategy_portfolio_data, strategy_trade_data  = misc_connect.query_uuid(uuid)
            res_dict[uuid] = {"data": list(strategy_data)[0], "portfolio": list(strategy_portfolio_data)[0], "trades": list(strategy_trade_data)[0]}

        fig = go.Figure()
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        store_portfolios = {}
        for key, value in res_dict.items():
            post_trade = PostTradeMetrics(value["data"]["ticker_1"], value["data"]["ticker_2"], value["data"]["start_date_trade"], value["data"]["end_date_trade"])
            post_trade.initialise_portfolio(value["portfolio"]["results"]["starting_capital"], value["portfolio"]["results"]["historic_pnl"], value["portfolio"]["results"]["pnl"], value["portfolio"]["results"]["growth"])
            post_trade.initialise_trades(value["trades"])

            store_portfolios[key] = post_trade

        max_duration = 0
        # Metric 1: Sharpe Ratio
        fig1 = go.Figure()
        fig1.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        for key, value in store_portfolios.items():
            hist_sharpe = value.historic_sharpe_ratio(risk_free_rate)
            fig1.add_trace(go.Scatter(x = np.linspace(0,1,len(hist_sharpe,)), y=hist_sharpe, mode='lines', name=f"{key}",  showlegend=False))
            
            if len(hist_sharpe) > max_duration:
                max_duration = len(hist_sharpe)
        fig1.update_layout(yaxis_title="Sharpe Ratio", xaxis_title="Time", margin=dict(l=0, r=0, t=36, b=0))

        # Metric 2: Max Drawdown
        fig2 = go.Figure()
        fig2.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        for key, value in store_portfolios.items():
            max_drawdown = value.historic_max_drawdown()
            fig2.add_trace(go.Scatter(x = np.linspace(0,1,len(max_drawdown,)), y=max_drawdown, mode='lines', name=f"{key}",  showlegend=False))
        fig2.update_layout(yaxis_title="Max Drawdown", xaxis_title="Trading Duration", margin=dict(l=0, r=0, t=36, b=0))

        # Metric 3: Calmar Ratio
        fig3 = go.Figure()
        fig3.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        for key, value in store_portfolios.items():
            calmar_ratio = value.historic_calmar_ratio()
            fig3.add_trace(go.Scatter(x = np.linspace(0,1,len(calmar_ratio,)), y=calmar_ratio, mode='lines', name=f"{key}",  showlegend=False))
        fig3.update_layout(yaxis_title="Calmar Ratio", xaxis_title="Trading Duration", margin=dict(l=0, r=0, t=36, b=0))

        # Metric 4: Sortino Ratio
        fig4 = go.Figure()
        fig4.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        for key, value in store_portfolios.items():
            sortino_ratio = value.historic_sortino_ratio(risk_free_rate, target_rate)
            fig4.add_trace(go.Scatter(x = np.linspace(0,1,len(sortino_ratio,)), y=sortino_ratio, mode='lines', name=f"{key}",  showlegend=False))

        fig4.update_layout(yaxis_title="Sortino Ratio", xaxis_title="Trading Duration", margin=dict(l=0, r=0, t=36, b=0))

            
        data = []
        for uuid in uuids[:14]:
            row = {
                "ID": uuid,
                "method": res_dict[uuid]["data"]["method"].split("Regression")[0],
                "length": len(res_dict[uuid]["portfolio"]["results"]["historic_pnl"]),
                "number_trade": len(res_dict[uuid]["trades"]["trades"]),
                "pnl": res_dict[uuid]["portfolio"]["results"]["growth"],
                "sharpe": float(np.round(store_portfolios[uuid].calculate_sharpe_ratio(risk_free_rate), 2)),
                "max_drawdown": float(np.round(store_portfolios[uuid].calculate_max_drawdown(), 2)),
                "calmar": float(np.round(store_portfolios[uuid].calculate_calmar_ratio(), 2)),
                "sortino": float(np.round(store_portfolios[uuid].calculate_sortino_ratio(risk_free_rate, target_rate), 2)),
            }
            data.append(row)

        table = dash_table.DataTable(
            data=data,
            columns=[{'name': 'ID', 'id': 'ID'},
                     {'name': 'Method', 'id': 'method'},
                     {'name': 'Length', 'id': 'length'},
                     {'name': 'N Trades', 'id': 'number_trade'},
                     {'name': 'PnL %', 'id': 'pnl'},
                     {'name': 'Sharpe', 'id': 'sharpe'},
                     {'name': 'Drawdown', 'id': 'max_drawdown'},
                     {'name': 'Calmar', 'id': 'calmar'},
                     {'name': 'Sortino', 'id': 'sortino'},],
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
        return fig1, fig2, fig3, fig4, table
















    @app.callback(
        Output('search-parameters', 'children'),
        Input('search-option', 'value'),
    )
    def update_search_parameters(option):
        if option == 'specific':
            return dbc.Row([
                dbc.Col(dcc.DatePickerRange(
                    id='training-dates',
                    min_date_allowed=datetime(2013, 1, 1),
                    max_date_allowed=datetime.today(),
                    initial_visible_month=datetime.today(),
                    start_date=datetime(2020, 6, 1),
                    end_date=datetime(2022, 6, 1),
                ), width="auto"),
                    dbc.Col(dcc.DatePickerRange(
                    id='trade-dates',
                    min_date_allowed=datetime(2013, 1, 1),
                    max_date_allowed=datetime.today(),
                    initial_visible_month=datetime.today(),
                    start_date=datetime(2022, 6, 2),
                    end_date=datetime(2023, 7, 1),
                ), width="auto"),
                dbc.Col([create_dropdown("ticker-options-main-1", names, ["CDMO", "GOLF"])], width=3),
                dbc.Col([dcc.Dropdown(id='method-selection-main-1', options=[{"label": "Kalman", "value": "Kalman", "search": "Kalman"},
                                                                      {"label": "OLS", "value": "OLS", "search": "OLS"}],
                                                                        placeholder='Method')], width=1),
                dbc.Col(dbc.Button(
                    "Load", id="submit-button-trade", color="primary"
                    ),
                    width="auto",
                    style={'overflow': 'visible', 'text-align': 'left'}
                )
            ])
        elif option == 'profitable':
            return dbc.Row([
                dbc.Col([dcc.Input(id='top-k', type='number', placeholder='Enter Top K', 
                                   style={
                                       'width': '100%',
                                       'height': '38px', # Match height with Dropdown (might need to adjust)
                                        'border': '1px solid #ced4da', # Similar border to typical Bootstrap dropdown
                                        'borderRadius': '0.25rem', # Rounded corners like Bootstrap dropdown
                                        'padding': '0.375rem 0.75rem', # Similar padding to Bootstrap dropdown
                                        'color': '#495057', # Font color similar to Bootstrap dropdown
                                        'backgroundColor': '#fff', # White background
                                       })], width=2),
                dbc.Col(dbc.Button(
                    "Load", id="submit-button-trade", color="primary"
                    ),
                    width="auto",
                    style={'overflow': 'visible', 'text-align': 'left'}
                )
            ])
        elif option == 'tickers':
            return dbc.Row([
                dbc.Col([create_dropdown("ticker-options-search-1", names, ["CDMO", "GOLF"])], width=4),
                dbc.Col(dbc.Button(
                    "Load", id="submit-button-trade", color="primary"
                    ),
                    width="auto",
                    style={'overflow': 'visible', 'text-align': 'left'}
                )
            ])
        elif option == 'method':
            return dbc.Row([
                dbc.Col([dcc.Dropdown(id='method-selection', options=[{"label": "Kalman", "value": "KalmanRegression", "search": "Kalman"},
                                                                      {"label": "OLS", "value": "OLSRegression", "search": "OLS"}],
                                                                        placeholder='Select Method')], width=4),
                dbc.Col(dbc.Button(
                    "Load", id="submit-button-trade", color="primary"
                    ),
                    width="auto",
                    style={'overflow': 'visible', 'text-align': 'left'}
                )
            ])
        elif option == 'uuid':
            return dbc.Row([
                dbc.Col([dcc.Input(id='uuid', placeholder='Copy/Paste UUID',
                                   style={
                                       'width': '100%',
                                       'height': '38px', # Match height with Dropdown (might need to adjust)
                                        'border': '1px solid #ced4da', # Similar border to typical Bootstrap dropdown
                                        'borderRadius': '0.25rem', # Rounded corners like Bootstrap dropdown
                                        'padding': '0.375rem 0.75rem', # Similar padding to Bootstrap dropdown
                                        'color': '#495057', # Font color similar to Bootstrap dropdown
                                        'backgroundColor': '#fff', # White background
                                       })], width=4),
                dbc.Col(dbc.Button(
                    "Load", id="submit-button-trade", color="primary"
                    ),
                    width="auto",
                    style={'overflow': 'visible', 'text-align': 'left'}
                )
            ])
    @app.callback(
        Output('uuid-storage-1', 'data'),
        Input('ticker-options-main-1', 'value'),
        Input('method-selection-main-1', 'value'),
        Input('training-dates', 'start_date'),
        Input('training-dates', 'end_date'),
        Input('trade-dates', 'start_date'),
        Input('trade-dates', 'end_date'),
    )
    def retrieve_specific_strategy(tickers, method, start_training_date, end_training_date, start_date_trade, end_date_trade):
        if tickers is None:
            raise PreventUpdate
        ticker_1, ticker_2 = tickers
        global uuids
        uuids = misc_connect.query_specific_strategy(ticker_1, ticker_2, method, start_training_date, end_training_date, start_date_trade, end_date_trade)

        return {'uuids': list(uuids)}

    @app.callback(
        Output('uuid-storage-2', 'data'),
        Input('top-k', 'value'),
    )
    def retrieve_most_profitable(top_k):
        if top_k is None:
            raise PreventUpdate
        
        global uuids
        uuids = misc_connect.query_most_profitable(top_k)
        return {'uuids': list(uuids)}

    @app.callback(
        Output('uuid-storage-3', 'data'),
        Input('ticker-options-search-1', 'value'),
    )
    def retrieve_by_tickers(tickers):
        if tickers is None:
            raise PreventUpdate
        ticker_1, ticker_2 = tickers
        global uuids
        uuids = misc_connect.query_by_tickers(ticker_1, ticker_2)
        return {'uuids': list(uuids)}

    @app.callback(
        Output('uuid-storage-4', 'data'),
        Input('method-selection', 'value'),
    )
    def retrieve_by_method(method):
        if method is None:
            raise PreventUpdate
        global uuids
        uuids = misc_connect.query_by_method(method)
        return {'uuids': list(uuids)}






















    # Hyperparameter constraints and quality of life callbacks
    @app.callback(
        Output('train-date-1', 'end_date'),
        Input('trade-date-1', 'start_date')
    )
    def update_train_end_date(start_trade_date):
        start_trade_date = date_handler(start_trade_date)
        start_trade_date = str_to_date(start_trade_date)
        return start_trade_date - timedelta(days=1)
    
    @app.callback(
        [Output('slider-sigma-sell-low', 'max'),
         Output('slider-sigma-sell-high', 'min')],
        Input('slider-sigma-buy', 'value')
    )
    def update_sliders_max(buy_sigma_value):
        return buy_sigma_value, buy_sigma_value

    
    @app.callback(
        [Output('slider-maxlen', 'max'),
         Output('slider-adf-window', 'max')],
        [Input('trade-date-1', 'start_date'),
         Input('trade-date-1', 'end_date')]
    )
    def update_maxlen_adf_window(start_date, end_date):
        start_date = date_handler(start_date)
        end_date = date_handler(end_date)
        number_of_days = (str_to_date(end_date) - str_to_date(start_date)).days
        return number_of_days, number_of_days
    
    
    
    
    # Update slider values for strategy hyperparameters
    @app.callback(
    Output('slider-sigma-buy-value', 'children'),
        Input('slider-sigma-buy', 'value')
    )
    def update_sigma_buy_slider(value):
        return f'\u03C3 Buy: {value:.2f}' 
    
    @app.callback(
    Output('slider-sigma-sell-low-value', 'children'),
        Input('slider-sigma-sell-low', 'value')
    )
    def update_sigma_sell_low_value(value):
        return f'\u03C3 Sell: {value:.2f}' 
    
    @app.callback(
    Output('slider-sigma-sell-high-value', 'children'),
        Input('slider-sigma-sell-high', 'value')
    )
    def update_sigma_sell_stop_value(value):
        return f'\u03C3 STOP: {value:.2f}' 
    

    @app.callback(
    Output('slider-maxlen-value', 'children'),
        Input('slider-maxlen', 'value')
    )
    def update_window_length_regr(value):
        return f'Window: {value:.2f}' 
    
    @app.callback(
    Output('slider-adf-window-value', 'children'),
        Input('slider-adf-window', 'value')
    )
    def update_adf_value(value):
        return f'ADF: {value:.2f}' 

    @app.callback(
    Output('slider-adf-pvalue-value', 'children'),
        Input('slider-adf-pvalue', 'value')
    )
    def update_adf_value(value):
        return f'p: {value:.3f}' 
    
    # Update slider values for port-trade hyperparameters

    @app.callback(
    Output('risk-free-rate-value', 'children'),
        Input('risk-free-rate', 'value')
    )
    def update_risk_free_rate(value):
        return f'Risk-Free Rate: {value:.3f}'
                              
    @app.callback(
    Output('target-return-value', 'children'),
        Input('target-return', 'value')
    )
    def update_target_return(value):
        return f'Target Return Buy: {value:.3f}'
    
    # Restricts to ticker pairs
    @app.callback(
        Output('trade-ticker-dropdown-1', 'value'),
        Input('trade-ticker-dropdown-1', 'value')
    )
    def limit_dropdown_selection(tickers):
        if len(tickers) > 2:
            return tickers[-2:]
        return tickers


   
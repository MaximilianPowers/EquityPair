from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from gui.utils import str_to_date
from finance.single_pair_strat.online_strategy import OnlineRegressionStrategy
from gui.utils import date_handler
import pandas as pd
import numpy as np


def register_trade_callbacks(app, data_fetcher, misc_connect):
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
                               maxlen, start_date_train, end_date_train,
                               start_date_trade, end_date_trade):
        if n is None or n == 0:
            fig_1 = go.Figure()
            fig_1.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            return fig_1, fig_1, fig_1, fig_1
        if tickers is None:
            if len(tickers) < 2:
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
                     "sell_sigma_high": sigma_sell_high, "maxlen": maxlen}
        method_name = method+"Regression"

        strategy = OnlineRegressionStrategy(method_name, CAPITAL, ticker_1, ticker_2, 
                                            start_date_train, end_date_train,
                                            start_date_trade, end_date_trade,
                                            hyperparameters, None)
        strategy.train_model()
        strategy.trade_model()
        strategy.post_trades(misc_connect)
                
        # Cointegration results
        COINT_MAXLEN = len(strategy.ts[strategy.ts["Mode"]== "Trade"].index)//10

        dates, p_values, coint_spread = strategy.run_cointegration_test(COINT_MAXLEN)

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

        store_pnl = []
        for record in trades_.keys():
            entry_date = trades_[record]['entry_date']
            exit_date = trades_[record]['trade_exit_date']
            long_ticker = trades_[record]['long_ticker']
            pnl = trades_[record]['pnl']
            duration = str_to_date(exit_date) - str_to_date(entry_date)

            if ticker_1 == long_ticker:
                store_pnl.append([str_to_date(exit_date), pnl, duration, "Normal"])
            else:
                store_pnl.append([str_to_date(exit_date), pnl, duration, "Swapped"])
        df = pd.DataFrame(store_pnl, columns = ["Date", "PnL", "Duration", "Mode"])
        df.index = df.Date
        # Calculate the cumulative sum for "Normal" mode
        df['NormalPnL'] = np.where(df['Mode'] == 'Normal', df['PnL'], 0).cumsum()

        # Calculate the cumulative sum for "Swapped" mode
        df['SwappedPnL'] = np.where(df['Mode'] == 'Swapped', df['PnL'], 0).cumsum()

        # Calculate the total cumulative sum
        df['TotalPnL'] = df['PnL'].cumsum()
        print(df)
        df.index = pd.to_datetime(df['Date'])
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x = df.index, y=df["NormalPnL"], mode='lines', name=f"Normal {ticker_1}/{ticker_2}"))
        fig2.add_trace(go.Scatter(x = df.index, y=df["SwappedPnL"], mode='lines', name=f"Swapped {ticker_2}/{ticker_1}"))
        fig2.add_trace(go.Scatter(x = df.index, y=df["TotalPnL"], mode='lines', name=f"Total"))
        fig2.update_layout(yaxis_title="Profit", xaxis_title="Time", margin=dict(l=0, r=0, t=36, b=0))




        res = np.array(strategy.store_res)

        # Create a Plotly figure
        fig3 = go.Figure()
        # Add line traces for each column in res
        fig3.add_trace(go.Scatter(y=res[:, 0], mode='lines', name="Normal Buy"))
        fig3.add_trace(go.Scatter(y=res[:, 1], mode='lines', name="Swapped Buy"))
        fig3.add_trace(go.Scatter(y=res[:, 2], mode='lines', name="Normal Sell"))
        fig3.add_trace(go.Scatter(y=res[:, 3], mode='lines', name="Swapped Sell"))
        fig3.add_trace(go.Scatter(y=coint_spread, mode='lines', name=f"Cointegration: {COINT_MAXLEN}"))

        if not np.isnan(res[:, 4]).any() and not np.isnan(res[:, 5]).any():
            fig3.add_trace(go.Scatter(y=res[:, 4], mode='lines', name="Normal StopLoss"))
            fig3.add_trace(go.Scatter(y=res[:, 5], mode='lines', name="Swapped StopLoss"))
        fig3.add_trace(go.Scatter(y=res[:, -1], mode='lines', name="Estimated Spread"))

        # Set title, x label, and legend position
        fig3.update_layout(yaxis_title="Spread", xaxis_title="Time", margin=dict(l=0, r=0, t=36, b=0))
        print('-'*50)
        print(f'For Pair Strategy: {ticker_1} / {ticker_2}')
        print(f"Training: {start_date_train} / {end_date_train}")
        print(f"Trading: {start_date_trade} / {end_date_trade}")
        print(f"Profit: {strategy.portfolio.pnl}")
        print(f"Trades: {len(strategy.portfolio.closed_trades)}")
        print('-'*50)


        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=dates, y=p_values, mode='lines', name="p-value"))
        fig4.update_layout(yaxis_title="Spread", xaxis_title="Time", margin=dict(l=0, r=0, t=36, b=0))
        return fig1, fig2, fig3, fig4

    @app.callback(
    Output('slider-sigma-buy-value', 'children'),
        Input('slider-sigma-buy', 'value')
    )
    def update_adf_value(value):
        return f'\u03C3 Buy: {value:.2f}' 
    
    @app.callback(
    Output('slider-sigma-sell-low-value', 'children'),
        Input('slider-sigma-sell-low', 'value')
    )
    def update_adf_value(value):
        return f'\u03C3 Sell: {value:.2f}' 
    
    @app.callback(
    Output('slider-sigma-sell-high-value', 'children'),
        Input('slider-sigma-sell-high', 'value')
    )
    def update_adf_value(value):
        return f'\u03C3 STOP: {value:.2f}' 
    
    @app.callback(
    Output('slider-maxlen-value', 'children'),
        Input('slider-maxlen', 'value')
    )
    def update_adf_value(value):
        return f'Window: {value:.2f}' 
    
    @app.callback(
        Output('trade-ticker-dropdown-1', 'value'),
        Input('trade-ticker-dropdown-1', 'value')
    )
    def limit_dropdown_selection(tickers):
        if len(tickers) > 2:
            return tickers[-2:]
        return tickers

   

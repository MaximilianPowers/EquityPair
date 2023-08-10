# TEST TO RUN THE STRATEGY

import pandas as pd
from finance.online_strategy import OnlineRegressionStrategy
import json
import numpy as np
import matplotlib.pyplot as plt
from data_loader.misc_connect import MongoConnect
from argparse import ArgumentParser
import os
parser = ArgumentParser()
parser.add_argument("--ticker_1", type=str, default="MD")
parser.add_argument("--ticker_2", type=str, default="EA")
parser.add_argument("--start_training_date", type=str, default="2020-06-01")
parser.add_argument("--end_training_date", type=str, default="2022-06-01")
parser.add_argument("--start_trading_date", type=str, default="2022-06-02")
parser.add_argument("--end_trading_date", type=str, default="2023-06-02")
parser.add_argument("--method", type=str, default="KalmanRegression")
args = parser.parse_args()

FIG_DIR = "{FIG_DIR}"

if not os.path.exists(FIG_DIR):
    os.makedirs(FIG_DIR)
    
m = MongoConnect()
capital  = 1_000_000
ticker_1 = args.ticker_1
ticker_2 = args.ticker_2

start_training_date = args.start_training_date
end_training_date = args.end_training_date

start_trading_date = args.start_trading_date
end_trading_date = args.end_trading_date

hyperparameters = {"buy_sigma": 1, "sell_sigma_low": 0.2,
                     "sell_sigma_high": 3, "maxlen": 1000}
method = args.method

if method not in ["KalmanRegression", "OLSRegression"]:
    raise ValueError("method must be either KalmanRegression or OLSRegression.")

if method == 'KalmanRegression':
    method_name = "Kalman"
if method == 'OLSRegression':
    method_name = "OLS"

strategy = OnlineRegressionStrategy(method, capital, ticker_1, ticker_2, 
                          start_training_date, end_training_date, 
                          start_trading_date, end_trading_date, 
                          hyperparameters, None)
strategy.train_model()
strategy.trade_model()

print(f"PnL: {strategy.portfolio.pnl}")
print(f"Number of trades: {len(strategy.portfolio.closed_trades)}")

with open("res_1.json", "w") as f:
    json.dump(strategy.portfolio.closed_trades, f)

strategy.post_trades(m)
ts1 = strategy.ts[strategy.ts["Mode"] == "Trade"][ticker_1]
ts1.index = pd.to_datetime(ts1.index)
ts2 = strategy.ts[strategy.ts["Mode"] == "Trade"][ticker_2]
ts2.index = pd.to_datetime(ts2.index)
fig, ax = plt.subplots(figsize=(30, 10))
ax.plot(ts1.index, ts1.values)
ax.plot(ts2.index, ts2.values)
ax.legend([ticker_1, ticker_2])
ax.set_title(f"{method_name} Pairs Trading Strategy")
# Trade entry details
for key in list(strategy.portfolio.closed_trades.keys()):
    trade = strategy.portfolio.closed_trades[key]
    entry_date = pd.to_datetime(trade["entry_date"])
    long_ticker = trade["long_ticker"]
    short_ticker = trade["short_ticker"]
    pnl = trade["pnl"]

    # Add entry marker and annotation
    ax.axvline(x=entry_date, color='green', linestyle='--')
    entry_annotation = f"Enter: Long {long_ticker}, Short {short_ticker}"
    
    ax.annotate(np.round(pnl, 2), (entry_date, ts1.loc[entry_date]), xytext=(10,-80), textcoords='offset points', arrowprops=dict(facecolor='green'))

    # Trade exit details
    exit_date = pd.to_datetime(trade["trade_exit_date"])

    # Add exit marker and annotation
    ax.axvline(x=exit_date, color='red', linestyle='--')
    exit_annotation = f"Exit: Long {long_ticker}, Short {short_ticker}"
    ax.annotate(exit_annotation, (exit_date, ts1.loc[exit_date]), xytext=(10,10), textcoords='offset points', arrowprops=dict(facecolor='red'))

# Remove x ticks:
ax.set_xticks([])

fig.savefig(f"{FIG_DIR}/res_1_{method_name.lower()}.png")


df = pd.read_json("res_1.json").transpose()
strategy.portfolio.closed_trades
fig, ax = plt.subplots()
ax.plot(np.cumsum(df["pnl"].values))
ax.set_title("PnL over time")
ax.set_xlabel("Time")
ax.set_ylabel("PnL")
fig.savefig(f"{FIG_DIR}/res_2_{method_name.lower()}.png")


res = np.array(strategy.store_res)
fig, ax = plt.subplots()
ax.plot(res[:, 0], label="Normal Buy")
ax.plot(res[:, 1], label="Swapped Buy")
ax.plot(res[:, 2], label="Normal Sell")
ax.plot(res[:, 3], label="Swapped Sell")
ax.plot(res[:, 4], label="Spread")
ax.legend()
ax.set_title(f"{method_name} Regression Trading Strategy")
ax.set_xlabel("Time")
# Set legend position
ax.legend(loc='upper right', bbox_to_anchor=(1.05, 1))
fig.savefig(f"{FIG_DIR}/res_3_{method_name.lower()}.png")

fig, ax = plt.subplots()
ax.plot(res[:, -2], label="Alpha")
ax.plot(res[:, -1], label="Beta")
ax.legend()
ax.set_title(f"{method_name} Regression Trading Strategy")
ax.set_xlabel("Time")
# Set legend position
ax.legend(loc='upper right', bbox_to_anchor=(1.05, 1))
fig.savefig(f"{FIG_DIR}/res_4_{method_name.lower()}.png")


import pandas as pd
from finance.single_pair_strat.online_strategy import OnlineRegressionStrategy
import json
import numpy as np
import matplotlib.pyplot as plt
from data_loader.misc_connect import MongoConnect

m = MongoConnect()
capital  = 1_000_000
ticker_1 = "MD"
ticker_2 = "EA"

start_training_date = "2020-06-01"
end_training_date = "2022-06-01"

start_trading_date = "2020-06-02"
end_trading_date = "2023-06-02"

hyperparameters = {"buy_sigma": 1, "sell_sigma_low": 0.1, 
                   "sell_sigma_high": np.inf, "delta": 1e-5, 
                   "maxlen": 100, "static": False}
method = "KalmanRegression"
strategy = OnlineRegressionStrategy(method, capital, ticker_1, ticker_2, start_training_date, end_training_date, start_trading_date, end_trading_date, hyperparameters, None)
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
ax.set_title("Kalman Filter Trading Strategy")
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

fig.savefig('res_1.png')

df = pd.read_json("res_1.json").transpose()
strategy.portfolio.closed_trades
fig, ax = plt.subplots()
ax.plot(np.cumsum(df["pnl"].values))
ax.set_title("PnL over time")
ax.set_xlabel("Time")
ax.set_ylabel("PnL")
fig.savefig("res_2.png")

res = np.array(strategy.store_res)
fig, ax = plt.subplots()
ax.plot(res[:, 0], label="Normal Buy")
ax.plot(res[:, 1], label="Swapped Buy")
ax.plot(res[:, 2], label="Normal Sell")
ax.plot(res[:, 3], label="Swapped Sell")
ax.plot(res[:, 4], label="Spread")
ax.legend()
ax.set_title("Kalman Filter Trading Strategy")
ax.set_xlabel("Time")
# Set legend position
ax.legend(loc='upper right', bbox_to_anchor=(1.05, 1))
fig.savefig("res_3.png")

fig, ax = plt.subplots()
ax.plot(res[:, -2], label="Alpha")
ax.plot(res[:, -1], label="Beta")
ax.legend()
ax.set_title("Kalman Filter Trading Strategy")
ax.set_xlabel("Time")
# Set legend position
ax.legend(loc='upper right', bbox_to_anchor=(1.05, 1))
fig.savefig("res_4.png")


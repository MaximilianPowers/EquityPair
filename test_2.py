import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from finance.single_pair_strat.kalman import KalmanStrategy
from datetime import datetime, timedelta
import json

hyperparameters = {"buy_sigma": 2, "sell_sigma_low": .001, "sell_sigma_high": np.inf, "delta": 1e-5, "maxlen": 10000, "static": False}

# Create some dummy data
np.random.seed(42)
dates = pd.date_range(start="2021-01-01", periods=100, freq='D').astype(str)
ticker_1_data = np.sin(np.linspace(0, 10, 100)) + np.random.normal(scale=0.1, size=100)-0.5
ticker_2_data = np.sin(np.linspace(0, 10, 100)) + np.random.normal(scale=0.1, size=100)
start_training_date = '2021-01-01'
end_training_date = dates[-1]

# Create a DataFrame
ts_data = pd.DataFrame({
    'Date': dates,
    'MSFT': ticker_1_data,
    'AMZN': ticker_2_data,
    'Mode': 'Train'
})

dates = pd.date_range(start="2022-01-01", periods=100, freq='D').astype(str) 
a = np.zeros(100)
a[:10] = 1
ticker_1_data = a + np.sin(np.linspace(1, 10, 100)) + np.random.normal(scale=0.1, size=100)-0.5
ticker_2_data = np.sin(np.linspace(0, 10, 100)) + np.random.normal(scale=0.1, size=100)

# Create a DataFrame
ts_data = pd.concat((ts_data, pd.DataFrame({
    'Date': dates,
    'MSFT': ticker_1_data,
    'AMZN': ticker_2_data,
    'Mode': 'Trade'
})))

ts_data.index = ts_data['Date']

# Assuming you've defined a KalmanStrategy class and related methods

capital = 100000
ticker_1 = 'MSFT'
ticker_2 = 'AMZN'

start_date = '2022-01-01'
end_date = dates[-1]

strategy = KalmanStrategy(
    capital, 
    ticker_1, 
    ticker_2, 
    start_training_date, 
    end_training_date, 
    start_date, 
    end_date,
    hyperparameters,
    ts_data # assuming your constructor takes the DataFrame or adjust as necessary
)

strategy.train_model()
strategy.trade_model()
with open("res_1.json", "w") as f:
    json.dump(strategy.portfolio.closed_trades, f)

print(f"PnL: {strategy.portfolio.pnl}")
print(f"Number of trades: {len(strategy.portfolio.closed_trades)}")

# Assuming your portfolio method displays the results
#strategy.portfolio.plot_portfolio()

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
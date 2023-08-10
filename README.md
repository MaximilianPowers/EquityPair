<h1> Equity Pairs Trading GUI </h1>
---------------------

This is a Dash GUI for exploring Equity Pair trading on a pool of candidates from the 
S&P 500, NASDAQ 100 and Russell 2000 tickers. 

## Installation
---------------------
Use the package manager [pip](https://pip.pypa.io/en/stable/) install the dependencies .

```bash
pip install -r requirements.txt
```

This GUI uses MongoDB to store ticker data and record trading strategies, portfolios, etc. 

## Running the interface
---------------------

All the code is centrally managed from `main.py`:
optional arguments:
  --mongo_host localhost
                        Hostname of the MongoDB databse.
  --mongo_port 27017
                        Port to connect to MongoDB.
  --db_name equity_data 
                        Nmae of the database to add data to.
  --load_data False
                        Set this equal to `True` on the first run to batch insert
                        ticker data. This will make the GUI experience much smoother.
  --start_date "2019-07-01"
                        Start date to batch insert data from
  --end_date "2022-07-01"
                        End date to batch insert data to
  --ticker_path "./utils/ticker.json"
                        Path to store the 2323 found tickers (1780/2000 Russell, 
                        100/100 NASDAQ 100, 500/500 S&P 500)

The `main.py` file sets up the database connections and once set up, runs the
`dashboard.py` file which is where the Dash interface is set up. 

## File Structure
---------------------

We've broken our web app into several components:
* `./analytics/`: 
  * `cluster_ticker.py`: Performs clustering on Tickers via 4 different methods to reduce the space of total possible combinations of pairs. The Self-Organising Maps Method (SOM) uses an unsupervised learning technique to cluster time series data sets. The results are quite promising an reduce our search space significantly.
  * `identify_tickers.py`: Given a set of clusters, run all possible combinations within that cluster to rank the pairs by mean reversion, cointegration and Hurst exponent.
  * `regression.py`: The methods used to run Kalman, Cointegration and OLS in an Online setting to constantly update our trading strategy.
  * `time_series.py`: This method is where we calculate the mean reversion and Hurst exponent.
* `./data_loader/`:
  * `data_loader.py`: MongoDB connector used to post ticker data to the database.
  * `get_data.py`: MongoDB connector used to retrieve ticker data from the database.
  * `misc_connect.py`: MongoDB connector used to post and retrieve portfolio, strategy and clustering results.
  * `singleton.py`: Ensures we only use one of each of the above connections throughout our session.
* `./finance/`:
  * `online_strategy.py`: Where we run our Kalman or OLS Equity Pairs strategy from given two tickers, a training duration and trading duration.
  * `portfolio_single.py`: Used to store the metadata related to our trading activities such as PnL, trading dates etc.
  * `portfolio.py`: Used to connect with the `Strategy` class to connect a trading strategy to a portfolio.
  * `post_trade_analysis.py`: Risk management scripts that can be run post a trading strategy to evaluate a strategy once it's finished.
  * `strategy.py`: Used to connect a strategy to a `Portfolio` class.
* `./gui/`: This folder stores all the related code for the interface, including most of the visualisation scripts. It's comprised currently of two screens: `screen_1` for analysis side and `screen_2` for the trading execution. Each folder will have a `layout.py` file storing the static layout of the page and a `callback.py` file that manages all the callbacks. We also have some utility functions for repetitive objects.
* `./tests/`: Currently holds a single test to run a simple trading strategy. Used for fine-tuning of the methods in `./gui/`.
* `./utils/`: Stores a list of downloaded Russell 2000 tickers (`russell_2000.xlsx`) and has methods to retrieve the components of the S&P 500 and NASDAQ 100.
* `dashboard.py`: Code to load the front page of the dashboard, hamburger menu and load the css from `./assets/`.


As mentioned previously, the GUI can be broken into 2 separate pages.

## Financial Analysis ##
---------------------


### Identifying Stationary & Mean Reverting Series ###

This section has two functions, firstly you can add any ticker (searchable). Once you've submitted that ticker information is stored in a table with relevant metrics and information about the ticker. 

### Ticker Clustering ###

This is where we reduce the search space of running our pair-wise analysis. Instead of computing all possible pairs, we narrow it down to pairs within a single cluster. There are 4 methods for clustering:
* Self-Organising Maps: Using unsupervised learning, we cluster the various time-series by features. 
* Industry: This breaks the tickers down into the various industries they are in from their yfinance metadata.
* Sector: This breaks the tickers down into the various sectors they are in from their yfinance metadata.
* Market Cap: This buckets all the tickers into 10 quantile-clusters based off their Market Cap, with Cluster 10 having the largest. 

Keep in mind these methods take some time to ingest all the related data

When performing trading strategies, be wary to keep the end date before the beggining of trading to not have any leakage of information.

Once submitted, we can then visualise these clusters by first picking an averaging method, choosing the cluster to visualise (left figure) and choosing a Group by operation to colour the clusters by some other related information, for instance to see a Market Cap breakdown of a SOM clustering.

### Pair Identification ### 

Now that we've got our clusters, load them in and then choose one of the clusters and get the hurst exponent, mean reversion coefficient, and perform cointegration tests. Keep in mind this may take a while.

Once finished click the Load button and from the dropdown click the pair identification you just ran (or any other). Then using the sliders, weight the importance of the 3 metrics as well as the number of results to be displayed in the table.

There should be a coloured table (by quantile distribution, green is good, red is bad). To the right are a few distribution plots to measure the whole cluster's pair-wise metrics to compare.

### Compute Hedging Ratio ###

This is where given two tickers, we can look into what Kalman filtering or OLS is doing, and how it projects one time series onto another. On the right we see a normalised graph of the two tickers as well as the thresholds set by OLS vs. Kalman. We can also get the current coefficients for beta for the OLS and Regression model, as well as the Cointegration score.

## Trading Simulation ##

Herein lies the dashboard to simulate the trading of an equity pairs strategy.

### Run Single Pair Strategies ###

Using either a Kalman or OLS method, runs the equity-pair strategy on two tickers. Note the sliders include when to exit, when to sell for a profit and a stop loss based off threshold. We also have a slider to control how farback the methods look in the time-series (keep in mind these are run in an online setting) and a slider for the ADF window to measure cointegration. Keep in mind we start with a capital of 10,000,000.

There is a main plot which displays when we enterred and exitted a trade, as well as if we went the normal option (short ticker 1, long ticker 2) or the swapped option (short ticker 2, long ticker 1). It also displays the PnL for the trade. Keep in mind we've capped the trades at 40% of the current portfolio value to reduce risk, this can be finetuned from the `portfolio.py` file. To the right we plot the value of the portfolio overtime

On the bottom left we have the thresholding plot to monitor the evolution of the thresholds throughtout trading. On the bottom right the p-value of the ADF plot.

### Post-Trade Analysis ###

Firstly, we find the strategy we want to analyse via various techniques. Then given a risk free rate and target return, we plot the four metrics: sharpe, max drawdown, calmar and sortino. We also aggregate these strategies and store them to the left, displaying various metadata.

##  Page
---------------------
The first page you're directed to is a main page which is where we will do most of
our investigation to identify which tickers are promising as candidates for an equity
pair strategy. 
```
## Usage
---------------------
Everything is managed from main.py. When running the 

```
EquityPair
├─ analytics
│  ├─ __init__.py
│  ├─ cluster_tickers.py
│  ├─ identify_tickers.py
│  ├─ regression.py
│  └─ time_series.py
├─ assets
│  └─ important.css
├─ data_loader
│  ├─ __init__.py
│  ├─ data_loader.py
│  ├─ get_data.py
│  ├─ misc_connect.py
│  ├─ singleton.py
│  └─ tickers.json
├─ finance
│  ├─ .DS_Store
│  ├─ __init__.py
│  ├─ figs
│  │  ├─ res_1_kalman.png
│  │  ├─ res_1_ols.png
│  │  ├─ res_2_kalman.png
│  │  ├─ res_2_ols.png
│  │  ├─ res_3_kalman.png
│  │  ├─ res_3_ols.png
│  │  ├─ res_4_kalman.png
│  │  ├─ res_4_ols.png
│  │  └─ res_good_kalman.png
│  ├─ online_strategy.py
│  ├─ portfolio.py
│  ├─ portfolio_single.py
│  ├─ post_trade_analysis.py
│  └─ strategy.py
├─ gui
│  ├─ __init__.py
│  ├─ screen_1
│  │  ├─ __init__.py
│  │  ├─ callbacks.py
│  │  └─ layout.py
│  ├─ screen_2
│  │  ├─ __init__.py
│  │  ├─ callbacks.py
│  │  └─ layout.py
│  └─ utils.py
├─ tests
│  └─ test.py
├─ utils
│  ├─ __init__.py
│  ├─ batch_insert.py
│  ├─ index_stocks.py
│  ├─ russell_2000.xlsx
│  ├─ tickers.json
│  └─ utils.py
├─ main.py
├─ notebook.ipynb
├─ requirements.txt
└─ README.md

```
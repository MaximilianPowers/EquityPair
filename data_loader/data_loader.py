from pymongo import MongoClient, errors, ASCENDING
from yfinance import download, Ticker
from datetime import datetime
from tqdm import tqdm
class SetStockData:
    """
    Class to download closing data from yfinance and writ to a MongoDB database.

    It's optimised for reading data, so each collection is a unique ticker with a list of dates and closing prices. Most of the code is to 
    handle the edge cases of updating the database.

    The database is structured as follows:
    - There is a collection for the price data "price_data", which is a timeseries collection.
    - There is a collection for the datetime metadata "date_data", which contains the earliest and latest dates for which data is available for each ticker.
    - There is a collection for the ticker metadata "ticker_data", which contains the tickers that are available in the database from yfinance .info() such as 
    industry, market cap, number of employees etc.
    
    """
    def __init__(self, db_name = "equity_data", collection_name="price_data", date_collection_name="date_data",  meta_collection_name="ticker_data", mongo_url="mongodb://localhost:27017/"):
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.date_collection = self.db[date_collection_name]
        self.meta_collection = self.db[meta_collection_name]

        try:
            self.db.create_collection(collection_name)
            self.db[collection_name].create_index([("ticker", ASCENDING), ("closing_prices.date", ASCENDING)])

        except errors.CollectionInvalid:
            pass  # Collection already exists

    def initialise_metadata(self, ticker):
        try:
            info = Ticker(ticker).info
        except:
            info = None
        query = {"_id": ticker} # or whatever your _id value is
        update = {"$set": {
            "_id": ticker,
            "info": info
        }} # replace 'your_document' with the actual document you want to insert/update
        self.meta_collection.update_one(query, update, upsert=True)

    def initialise_date_range(self, ticker, start_date, end_date):

        query = {"_id": ticker} # or whatever your _id value is
        update = {"$set": {
            "_id": ticker,
            "earliest_date": start_date,
            "latest_date": end_date
        }} # replace 'your_document' with the actual document you want to insert/update
        self.date_collection.update_one(query, update, upsert=True)

    def get_data_date_range(self, ticker):
        meta = self.date_collection.find_one({"_id": ticker})
        if meta is not None:
            return meta["earliest_date"], meta["latest_date"] 
        else:
            return None, None
    
    def download_data(self, ticker, start_date, end_date):
        data = download(ticker, start=start_date, end=end_date)
        if data.empty:
            print(f"No new data to download for {ticker}")
            return None

        closing_prices = [{"date": index.to_pydatetime(), "price": row["Close"]} for index, row in data.iterrows()]
        return closing_prices


    def update_single_ticker(self, ticker):
        earliest_data_date, last_data_date = self.get_data_date_range(ticker)
        earliest_data_date_dt = self.str_to_date(earliest_data_date)
        last_data_date_dt = self.str_to_date(last_data_date)

        if earliest_data_date is None and last_data_date is None:
            data = self.download_data(ticker, self.start_date, self.end_date)
            if data is not None:
                self.collection.update_one(
                    {"_id": ticker},
                    {
                        "$push": {
                            "price": {
                                "$each": data
                            }
                        },
                    },
                    upsert=True,
                )
                self.initialise_date_range(ticker, self.start_date, self.end_date)
                self.initialise_metadata(ticker)
            return

        if self.start_date_dt < earliest_data_date_dt:
            data = self.download_data(ticker, self.start_date, self.date_to_str(earliest_data_date_dt))
            if data is not None:
                self.collection.update_one(
                    {"_id": ticker},
                    {
                        "$push": {
                            "closing_prices": {
                                "$each": data,
                                "$position": 0
                            }
                        },
                    },
                    upsert=True,
                )
                self.date_collection.update_one(
                    {"_id": ticker},
                    {
                        "$set": {
                            "earliest_date": self.start_date,
                        }
                    }
                )

        if last_data_date_dt < self.end_date_dt:
            data = self.download_data(ticker, self.date_to_str(last_data_date_dt), self.end_date)
            if data is not None:
                self.collection.update_one(
                    {"_id": ticker},
                    {
                        "$push": {
                            "closing_prices": {
                                "$each": data
                            }
                        },
                    },
                    upsert=True,
                )
                self.date_collection.update_one(
                    {"_id": ticker},
                    {
                        "$set": {
                            "latest_date": self.end_date
                        }
                    }
                )


    def update_data(self, tickers, start_date, end_date):
        self.start_date_dt = self.str_to_date(start_date)
        self.end_date_dt = self.str_to_date(end_date)
        self.start_date = start_date
        self.end_date = end_date

        for ticker in tickers:
            self.update_single_ticker(ticker)

    def update_single_data(self, ticker, start_date, end_date):
        self.start_date_dt = self.str_to_date(start_date)
        self.end_date_dt = self.str_to_date(end_date)
        self.start_date = start_date
        self.end_date = end_date

        self.update_single_ticker(ticker)

    def bulk_insert_data(self, tickers, start_date, end_date):
        """
        Only call this method when there is no other data in the mongodb database. It group downloads the yfinance data and inserts it into the database
        for a fixed date range regardless of whether there is data already in the database. We call this function at the initialisation to ensure we don't
        need to wait too long to start running operations. The pre-set date range is 2021-08-01 to 2023-08-01.
        """
        data = download(tickers, start=start_date, end=end_date, group_by="ticker")
        data = data.dropna(axis=1, how='all')

        tickers = set([ticker for ticker,_ in data.columns])
        print("Inserting bulk data into MongoDB... This may take a while.")
        for ticker in tqdm(tickers):
            ticker_data = data[ticker]
            closing_prices = [{"date": index.to_pydatetime(), "price": row["Close"]} for index, row in ticker_data.iterrows()]

            self.initialise_date_range(ticker, start_date, end_date)
            self.initialise_metadata(ticker)
            self.collection.update_one(
                {"_id": ticker},
                {
                    "$push": {
                        "closing_prices": {
                            "$each": closing_prices
                        }
                    },
                },
                upsert=True,
            )

    @staticmethod
    def str_to_date(date_str):
        if isinstance(date_str, str):
            return datetime.strptime(date_str, "%Y-%m-%d")
        else:
            return date_str

    @staticmethod
    def date_to_str(date):
        if date is None:
            return None
        return date.strftime("%Y-%m-%d")


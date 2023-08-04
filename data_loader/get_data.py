import pandas as pd
from pymongo import MongoClient
from datetime import datetime

class GetStockData:
    """
    Interface to retrieve data from MongoDB database.
    """
    def __init__(self, db_name = "equity_data", collection_name="price_data",  meta_collection_name="ticker_data", mongo_url="mongodb://localhost:27017/"):
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.meta_collection = self.db[meta_collection_name]
        self.start_date = None
        self.end_date = None
        self.start_date_dt = None
        self.end_date_dt = None

    def get_ticker_names(self):
        cursor = self.collection.find()
        return cursor.distinct("ticker")
    
    def get_data_date_range(self, ticker):
        if self.start_date_dt is not None:
            start_date = self.start_date_dt
        else:
            start_date = datetime(1900, 1, 1)
        if self.end_date_dt is not None:
            end_date = self.end_date_dt
        else:
            end_date = datetime(2100, 1, 1)
        cursor = self.collection.find({"ticker": ticker, "date": {"$gte": start_date , "$lte": end_date}})
        return cursor
    
    def get_ticker_field_info(self, ticker, field):
        meta = self.meta_collection.find_one({"_id": ticker, f"info.{field}": {"$exists": True}}, {f"info.{field}": 1})
        if meta is not None and 'info' in meta and field in meta['info']:
            return meta["info"][field]
        return None
                
        
    def get_ticker_info(self, ticker):
        meta = self.meta_collection.find_one({"_id": ticker})
        if meta is not None:
            return meta["info"]
        else:
            return None

    def get_data(self, ticker):
        cursor = self.get_data_date_range(ticker)
        df = pd.DataFrame(list(cursor))
        # Convert 'date' from string to datetime and set as index
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        return df
    
    def set_dates(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.start_date_dt = self.str_to_date(start_date)
        self.end_date_dt = self.str_to_date(end_date)

    def collate_dataset(self, tickers, start_date="2000-01-01", end_date = "2025-01-01"):
        """
        Collate a dataset from the database for a list of tickers and a date range.
        """
        self.set_dates(start_date, end_date)
        dfs = []
        for ticker in tickers:
            df = self.get_data(ticker)
            df['ticker'] = ticker
            dfs.append(df)
        return pd.concat(dfs)
    

    @staticmethod
    def str_to_date(date_str):
        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%Y-%m-%d')
        else:
            return None

    @staticmethod
    def date_to_str(date):
        if date is None:
            return None
        return date.strftime('%Y-%m-%d')
    
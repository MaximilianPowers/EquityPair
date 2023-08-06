import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
from data_loader.data_loader import SetStockData
from tqdm import tqdm
s = SetStockData()

class GetStockData:
    """
    Interface to retrieve data from MongoDB database.
    """
    def __init__(self, db_name = "equity_data", collection_name="price_data",  date_collection_name = "date_data", meta_collection_name="ticker_data", mongo_url="mongodb://localhost:27017/"):
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.meta_collection = self.db[meta_collection_name]
        self.date_collection = self.db[date_collection_name]
        self.start_date = None
        self.end_date = None
        self.start_date_dt = None
        self.end_date_dt = None


    def get_ticker_date_range(self, ticker):
        """
        Get the earliest and latest dates for which data is available for a given ticker.
        """
        cursor = self.date_collection.find_one({"_id": ticker})
        if cursor is None:
            return None, None
        earliest_date = cursor["earliest_date"]
        latest_date = cursor["latest_date"]
        return earliest_date, latest_date
    
    def get_latest_earliest_date(self, tickers):
        """
        Finds the latest earliest date and earliest latest date to create a minimal date range with 
        to run SOM on.
        """
        earliest_date = datetime.now()-timedelta(days=365*10)
        latest_date = datetime.now()
        for ticker in tickers:
            cur_earliest_date, cur_latest_date = self.get_ticker_date_range(ticker)
            cur_earliest_date_dt = self.str_to_date(cur_earliest_date)
            cur_latest_date_dt = self.str_to_date(cur_latest_date)
            if cur_earliest_date_dt is not None and cur_latest_date_dt is not None:
                print(ticker, cur_earliest_date_dt, cur_latest_date_dt)
                if cur_earliest_date_dt > earliest_date:
                    earliest_date = cur_earliest_date_dt
                if cur_latest_date_dt < latest_date:
                    latest_date = cur_latest_date_dt
        return earliest_date, latest_date
    
    def get_ticker_names(self):
        return sorted([doc['_id'] for doc in self.collection.find({}, {'_id': 1})])
    
    def get_data_date_range(self, ticker):
        cur_earliest_date, cur_latest_date = self.get_ticker_date_range(ticker)
        cur_earliest_date_dt = self.str_to_date(cur_earliest_date)
        cur_latest_date_dt = self.str_to_date(cur_latest_date)

        if self.start_date_dt is None:
            start_date = cur_earliest_date_dt
        else:
            if self.start_date_dt < cur_earliest_date_dt:
                s.update_single_data(ticker, self.start_date, cur_earliest_date)
            start_date = self.start_date_dt

        if self.end_date_dt is  None:
            end_date = cur_latest_date_dt
        else:
            if self.end_date_dt > cur_latest_date_dt:
                s.update_single_data(ticker, cur_latest_date, self.end_date)
            end_date = self.end_date_dt
        
        pipeline = [
            {"$match": {"_id": ticker}},
            {"$unwind": "$closing_prices"},
            {"$match": {"closing_prices.date": {"$gte": start_date , "$lte": end_date}}}
        ]
        
        cursor = list(self.collection.aggregate(pipeline))
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
        """
        
        """
        cursor = self.get_data_date_range(ticker)
        if len(cursor) == 0:
            return None

        df = pd.DataFrame([{"date": doc["closing_prices"]["date"], 
                            "close": doc["closing_prices"]["price"]} for doc in cursor])
        # Convert 'date' from string to datetime and set as index
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        return df.drop_duplicates()
    
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
        print("Getting data for tickers:", tickers)
        print("Date range:", self.start_date, self.end_date)
        print(self.start_date_dt, self.end_date_dt)

        dfs = []
        for ticker in tickers:
            df = self.get_data(ticker)
            df['ticker'] = ticker

            dfs.append(df)
        return pd.concat(dfs)
    
    def get_single_date_price(self, ticker, date):
        if isinstance(date, str):
            date = self.str_to_date(date)
        cursor = self.collection.find_one({"_id": ticker, 
                                           "closing_prices": {
                                               "$elemMatch": {"date": date}
                                            }}, 
                                          {"_id": 0, "closing_prices.$": 1})
        if cursor is not None and "closing_prices" in cursor and len(cursor["closing_prices"]) > 0:
            return cursor['closing_prices'][0]['price']
        else:
            return None
    
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
    
from data_loader.get_data import GetStockData
from data_loader.misc_connect import MongoConnect
from data_loader.data_loader import SetStockData


class DatabaseConnection:
    _instance = None
    
    def __new__(cls, mongo_url):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.data_setter = SetStockData(mongo_url=mongo_url)
            cls._instance.misc_connect = MongoConnect(mongodb_url=mongo_url)
            cls._instance.data_fetcher = GetStockData(cls._instance.data_setter, mongo_url=mongo_url)

        return cls._instance

def get_misc_connect():
    return DatabaseConnection._instance.misc_connect

def get_data_setter():
    return DatabaseConnection._instance.data_setter

def get_data_fetcher():
    return DatabaseConnection._instance.data_fetcher
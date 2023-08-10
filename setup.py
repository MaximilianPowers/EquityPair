from argparse import ArgumentParser
from data_loader.singleton import DatabaseConnection

parser = ArgumentParser()
parser.add_argument("--mongo_host", type=str, default="localhost")
parser.add_argument("--mongo_port", type=int, default=27017)
parser.add_argument("--start_date", type=str, default="2019-07-01")
parser.add_argument("--end_date", type=str, default="2023-07-01")
parser.add_argument("--ticker_path", type=str, default="./utils/tickers.json")
args = parser.parse_args()



MONGO_URL = f"mongodb://{args.mongo_host}:{args.mongo_port}/"

connection = DatabaseConnection(MONGO_URL)
misc_connect = connection.misc_connect
data_setter = connection.data_setter
data_fetcher = connection.data_fetcher

from utils.batch_insert import _batch_insert

print("Batch downloading data from Yahoo Finance...")
_batch_insert(args.start_date, args.end_date, args.ticker_path) 


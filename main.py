# DATABASE IMPORTS
from data_loader.singleton import DatabaseConnection

# MISC
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--mongo_host", type=str, default="localhost")
parser.add_argument("--mongo_port", type=int, default=27017)
parser.add_argument("--db_name", type=str, default="equity_data")

parser.add_argument("--load_data", action='store_true',
                    help="Set equal to True on the first run to batch load "\
                    "data from Yahoo finance into the database. It will load "\
                    "data between start_date and end_date. Set equal to False "\
                    "to skip this step when this script is run subsequently.")

parser.add_argument("--start_date", type=str, default="2019-07-01")
parser.add_argument("--end_date", type=str, default="2023-07-01")
parser.add_argument("--ticker_path", type=str, default="./utils/tickers.json")
args = parser.parse_args()



MONGO_URL = f"mongodb://{args.mongo_host}:{args.mongo_port}/"
# Usage
connection = DatabaseConnection(MONGO_URL)
misc_connect = connection.misc_connect
data_setter = connection.data_setter
data_fetcher = connection.data_fetcher

LOAD_DATA = args.load_data

if args.load_data:
    from utils.batch_insert import _batch_insert
    print("Batch downloading data from Yahoo Finance...")
    _batch_insert(args.start_date, args.end_date, args.ticker_path) 
    LOAD_DATA = False


from dashboard import run_dashboard

run_dashboard()
# DATABASE IMPORTS
from data_loader.singleton import DatabaseConnection

# MISC
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--mongo_url", type=str, default="mongodb://localhost:27017/")
parser.add_argument("--db_name", type=str, default="equity_data")
args = parser.parse_args()



MONGO_URL = args.mongo_url
# Usage
connection = DatabaseConnection(mongo_url=MONGO_URL, db_name=args.db_name)
misc_connect = connection.misc_connect
data_setter = connection.data_setter
data_fetcher = connection.data_fetcher

from dashboard import run_dashboard

run_dashboard()
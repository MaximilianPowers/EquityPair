# DATABASE IMPORTS
from data_loader.singleton import DatabaseConnection

# MISC
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--mongo_host", type=str, default="localhost")
parser.add_argument("--mongo_port", type=int, default=27017)
parser.add_argument("--db_name", type=str, default="equity_data")
args = parser.parse_args()



MONGO_URL = f"mongodb://{args.mongo_host}:{args.mongo_port}/"
# Usage
connection = DatabaseConnection(MONGO_URL)
misc_connect = connection.misc_connect
data_setter = connection.data_setter
data_fetcher = connection.data_fetcher

from dashboard import run_dashboard

run_dashboard()
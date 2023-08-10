from data_loader.singleton import get_data_setter
import json
from utils.index_stocks import gen_ticker_dict

data_setter = get_data_setter()

def _batch_insert(start_date, end_date, ticker_path):
    gen_ticker_dict(ticker_path)
    with open(ticker_path) as f:
        tickers = json.load(f)
    full_list = []
    for key in tickers.keys():
        full_list.extend(tickers[key])
    full_list = list(set(full_list))
    clean_list = []
    for ticker in full_list:
        if ticker is None:
            continue
        if ticker == '':
            continue
        if ticker == ' ':
            continue
        clean_list.append(ticker)
    data_setter.bulk_insert_data(full_list, start_date, end_date)
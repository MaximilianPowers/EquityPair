import json
import pandas as pd

def get_tickers_snp():
    """
    Get the list of tickers from Wikipedia of russel 2000
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    sp500 = pd.read_html(url)
    sp500_list = sp500[0]['Symbol']
    return sp500_list

def get_tickers_russel():
    """
    Get the list of tickers from Wikipedia
    """     

    df = pd.read_excel("./utils/russell_2000.xlsx")
    tickers = df["Ticker"].tolist()
    return tickers

def get_tickers_nasdaq():
    """
    Get the list of tickers from Wikipedia
    """
    url = "https://en.wikipedia.org/wiki/NASDAQ-100"
    nas100 = pd.read_html(url)
    nas100_list = nas100[4]['Ticker']
    return nas100_list

def gen_ticker_dict(ticker_path="./utils/tickers.json"):
    nas_tickers = get_tickers_nasdaq()
    snp_tickers = get_tickers_snp()
    russel_tickers = get_tickers_russel()

    nas_tickers = [ticker for ticker in nas_tickers if ticker is not None and ticker != ""]
    snp_tickers = [ticker for ticker in snp_tickers if ticker is not None and ticker != ""]
    russel_tickers = [ticker for ticker in russel_tickers if ticker is not None and ticker != ""]
    results = {
        "nasdaq": nas_tickers,
        "snp": snp_tickers,
        "russel": russel_tickers,
        "exchange": ["^GSPC", "^NDX", "^RUT"] 
    }

    json.dump(results, open(ticker_path, "w"))


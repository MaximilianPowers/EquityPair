from bs4 import BeautifulSoup
import requests
import json

def get_tickers_snp():
    """
    Get the list of tickers from Wikipedia of russel 2000
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    table = soup.find(id="constituents")
    table_rows = table.find_all("tr")
    tickers = []
    for tr in table_rows:
        td = tr.find_all("td")
        row = [i.text for i in td]
        if row:
            tickers.append(row[0][:-2])
    return tickers

def get_tickers_russel():
    """
    Get the list of tickers from Wikipedia
    """     

    with open("./data_loader/russell_2000.html", "r") as f:
        page = f.read()
    soup = BeautifulSoup(page, "html.parser")

    tickers = [i.text for i in soup.find_all("div", {"class":"ticker-area"})]
    return tickers

def get_tickers_nasdaq():
    """
    Get the list of tickers from Wikipedia
    """
    url = "https://en.wikipedia.org/wiki/NASDAQ-100"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    table = soup.find(id="constituents")
    table_rows = table.find_all("tr")
    tickers = []
    for tr in table_rows:
        td = tr.find_all("td")
        row = [i.text for i in td]
        if row:
            tickers.append(row[1])
    return tickers

nas_tickers = get_tickers_nasdaq()
snp_tickers = get_tickers_snp()
russel_tickers = get_tickers_russel()

results = {
    "nasdaq": nas_tickers,
    "snp": snp_tickers,
    "russel": russel_tickers,
    "exchange": ["^GSPC", "^NDX", "^RUT"] 
}

json.dump(results, open("./data_loader/tickers.json", "w"))
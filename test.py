import json
from data_loader.misc_connect import MongoConnect
from data_loader.get_data import GetStockData
from analytics_module.identify_tickers import IdentifyCandidates, ScoreCandidates
start_date='2020-06-01'
end_date = '2023-07-01'
method = 'Industry'
cluster = 'Biotechnology'
m = MongoConnect()
#data_fetcher = GetStockData()
#tickers = list(m.get_cluster(method, cluster, start_date, end_date))
#
#ticker_pairs = [[tickers[i], tickers[j]] for i in range(len(tickers)) for j in range(i+1, len(tickers))]
#
#df = data_fetcher.collate_dataset(tickers, start_date, end_date)
#df = df.pivot(columns='ticker', values='close')
#
#identify = IdentifyCandidates(ticker_pairs, df)
#identify.iterate_tickers()
#
#m.post_pairs_results(method, cluster, start_date, end_date, identify.score)
str_ = "Industry:Biotechnology:2023-07-01:2020-06-01"
method, cluster, start_date, end_date = str_.split(':')

scores = m.get_pairs_results(method, cluster, start_date, end_date)
for key, value in dict(scores).items():
    print(scores[key]["coint"])
#s = ScoreCandidates(1/3, 1/3, 1/3, 15, identify.score)
#
#rankings = s.get_top_candidates()


from data_loader.get_data import GetStockData
from analytics_module.time_series import PairAnalyzer, TimeSeries
from data_loader.data_loader import SetStockData
import json

def main():
    with open('./data_loader/tickers.json') as f:
        tickers = json.load(f)
    full_list = []
    for key in tickers.keys():
        full_list.extend(tickers[key])
    full_list = list(set(full_list))[:100]
    start_date = '2023-06-01'
    end_date = '2023-07-01'
    s = GetStockData()

    df = s.collate_dataset(full_list, start_date, end_date)
    df_pivot = df.pivot(columns='ticker', values='close')
    df_pivot = df_pivot.dropna(axis=1)

    stationary_list = []
    mean_reversion_list = []
    for i in range(len(df_pivot.columns)):
        ticker1 = df_pivot.columns[i]

            
        pa = TimeSeries(df_pivot[ticker1].values, ticker1)
        bol, hurst = pa.check_for_mean_reversion()
        mean_reversion_list.append(hurst)

        bol, stat = pa.check_for_stationarity()
        stationary_list.append(stat)

    mr = sorted(range(len(mean_reversion_list)), key=mean_reversion_list.__getitem__)
    s_ = sorted(range(len(stationary_list)), key=stationary_list.__getitem__)
    print('Stationary')
    print(s_[:5])
    print('Mean Reversion')
    print(mr[:5])
    print(mean_reversion_list)






if __name__ == '__main__':
    main()
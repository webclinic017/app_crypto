# backtesting.py
# backtesting page


import os
import math
import time
import numpy as np
import pandas as pd

import datetime
import quantstats as qs
from datetime import date
from collections import defaultdict
from utilities.DB_connection import init_tcp
from utilities.common_data_retrieving import get_table_download_link, load_overall, load_dataset
from strategy.filter import get_indicators, filter_onePeriod, unique_selection_30, month_distribution, \
    get_future_daily_ret_multiple, stop_loss, after_buy_multiple
from strategy.portfolio import backtester_engine


def portfolio(filter_csv,
              dataset,
              tcp,
              start_date,
              end_date,
              price_lower_limit,
              short_term_ret_lower,
              short_term_ret_upper,
              long_term_ret_lower,
              long_term_ret_upper,
              avg_daily_dollar_vol_lower,
              median_daily_volume_lower,
              avg_daily_dollar_vol_upper,
              median_daily_volume_upper,
              dollar_vol_ratio_lower,
              price_upper_limit,
              dollar_vol_ratio_upper,
              range_test,
              dropdown_allow_in_gain,
              stop_loss_test_period,
              stop_gain_test_period,
              cash,
              slippage,
              max_weight,
              min_weight,
              benchmark,
              report_name):

    reserch = filter_onePeriod(dataframe=filter_csv,
                               start_date=start_date,
                               end_date=end_date,
                               price_lower_limit=price_lower_limit,
                               price_upper_limit=price_upper_limit,
                               short_term_ret_lower=short_term_ret_lower,
                               short_term_ret_upper=short_term_ret_upper,
                               long_term_ret_lower=long_term_ret_lower,
                               long_term_ret_upper=long_term_ret_upper,
                               avg_daily_dollar_vol_lower=avg_daily_dollar_vol_lower,
                               avg_daily_dollar_vol_upper=avg_daily_dollar_vol_upper,
                               median_daily_dollar_vol_lower=median_daily_volume_lower,
                               median_daily_dollar_vol_upper=median_daily_volume_upper,
                               dollar_vol_ratio_lower=dollar_vol_ratio_lower,
                               dollar_vol_ratio_upper=dollar_vol_ratio_upper)

    reserch = reserch[reserch['stocks'] != 'USDT-USD']
    symbols = reserch['stocks'].to_list()
    dates = reserch['date'].dt.strftime('%Y-%m-%d').to_list()
    after_buy = after_buy_multiple(symbols, dates, tcp=tcp, range_test=range_test,
                                   stop_loss_test_period=stop_loss_test_period,
                                   stop_gain_test_period=stop_gain_test_period,
                                   dropdown_allow_in_gain=dropdown_allow_in_gain,
                                   slippage=slippage)
    res = defaultdict(list)
    for sub in after_buy:
        for key in sub:
            res[key].append(sub[key])
    stop_loss_ret = dict(res)
    # replace
    reserch['cumulative_return_holdingPeriod'] = stop_loss_ret['cum_rets']
    reserch['max_price_during_holding_period'] = stop_loss_ret['max_prices']
    reserch['min_price_during_holding_period'] = stop_loss_ret['min_prices']
    reserch['actual_holding_period'] = stop_loss_ret['actual_holdings']
    # run the engine
    reserch['date'] = reserch['date'].astype(str)
    engine = backtester_engine(overall=reserch, dataset=dataset, start_date=start_date,
                               end_date=end_date, cash=cash, transactions_cost=slippage / 100,
                               max_weight=max_weight, min_weight=min_weight)
    engine.run()
    # get portfolio_rets
    portfolio_values = np.array(engine.cash_series) + np.array(engine.portfolio_stocks_value_series)
    portfolio_rets = pd.Series(portfolio_values,
                               index=[datetime.datetime.strptime(i, "%Y-%m-%d") for i in engine.timeline]).pct_change(1)
    # generate and save the templates

    qs.reports.html(portfolio_rets, benchmark=benchmark, output=os.path.join('for_loop_otput', report_name),
                    title='Crypto Strategy Tearsheet')  # ! TODO change save path

    # time.sleep(3)

    dates = []
    trans_types = []
    symbols = []
    dollar_vols = []
    prices = []
    stock_vals = []
    pct_changes = []
    cash_balances = []
    portfolio_balances = []
    holding_periods = []
    sell_dates = []
    for cur_rec in engine.record_logs:
        dates.append(cur_rec['cur_date'])
        trans_types.append(cur_rec['trans_type'])
        symbols.append(cur_rec['symbol'])
        dollar_vols.append(cur_rec['dollar_vol'])
        prices.append(cur_rec['price'])
        stock_vals.append(cur_rec['stock_val'])
        pct_changes.append(cur_rec['pct_change'])
        cash_balances.append(cur_rec['cash_balance'])
        portfolio_balances.append(cur_rec['portfolio_balance'])
        sell_dates.append(cur_rec['sell_date'])
        holding_periods.append(cur_rec['holding_days'])
    trading_logs = pd.DataFrame(
        {'Date': dates, 'Type': trans_types, 'Symbols': symbols, 'Dollar_vol': dollar_vols, 'Price': prices,
         'Stock_Value': stock_vals,
         "Pct_change": pct_changes, 'Cash_balance': cash_balances, "Portfolio_balance": portfolio_balances,
         'Sell_Date': sell_dates, "Holding_Period": holding_periods, })
    trading_logs = trading_logs.drop_duplicates()

    return trading_logs, reserch


if __name__ == "__main__":
    # initialize
    tcp = init_tcp()
    benchmark = qs.utils.download_returns('BTC-USD')
    filter_csv = load_overall()
    datasets = load_dataset(dir_path=os.path.join('data', 'csv'))


    start_date =['2015-05-26','2015-05-27', '2015-05-27', '2015-05-28', '2015-05-28', '2015-05-28', '2015-05-28', '2015-05-29', '2015-05-30']
    end_date = ['2021-05-17', '2021-05-18','2021-05-18', '2021-05-19', '2021-05-19', '2021-05-19', '2021-05-20', '2021-05-20', '2021-05-21']
    price_lower_limit = [0.01] * 9

    price_upper_limit = [100000] * 9

    short_term_ret_lower = [-0.9, 0.25, 0.25, 0.25, 0.25, 0.25, 0.5, 0.15, 0.5]
    short_term_ret_upper =[10]*9
    long_term_ret_lower = [-0.9, -0.9, -0.9, -0.9, -0.9, 0, -0.9, 1.0, 0]
    long_term_ret_upper = [100] * 9
    avg_daily_dollar_vol_lower = [1000000]*9
    median_daily_volume_lower = [1000000]*9
    avg_daily_dollar_vol_upper = [1000000000000000000000000000000] * 9
    median_daily_volume_upper = [1000000000000000000000000000000] * 9
    dollar_vol_ratio_lower = [0.5, 0.5, 0.5, 0.5, 2.0, 2.0, 2.0, 2.0, 2.0]
    dollar_vol_ratio_upper = [100] * 9
    range_test = [45] * 7 + [5] * 2
    dropdown_allow_in_gain = [30] * 7 + [15, 30]
    stop_loss_test_period = [99, 99, 8, 8, 8, 8, 8, 20, 7]
    stop_gain_test_period = [1000] * 3 + [50] * 4 + [25, 25]
    cash = [100000] * 9
    slippage = [0] * 9
    max_weight =[10] * 9
    min_weight = [8] * 9
    report_name = [f"{i}.html"] * 9
    log_name = [f"{i}.html"] * 9
    for i range(9):
        variable = portfolio(filter_csv,
                             dataset,tcp,
                             start_date =[i],
                             end_date = [i],
                             price_lower_limit = [i],
                             price_upper_limit = [i], short_term_ret_lower = [i],
                      short_term_ret_upper =[i],
                      long_term_ret_lower = [i],
                      long_term_ret_upper = [i],
                      avg_daily_dollar_vol_lower = [i],
                      median_daily_volume_lower = [i],
                      avg_daily_dollar_vol_upper = [i],
                      median_daily_volume_upper = [i],
                      dollar_vol_ratio_lower = [i],
                      dollar_vol_ratio_upper = [i],
                      range_test = [i],
                      dropdown_allow_in_gain =[i],
                      stop_loss_test_period = [i],
                      stop_gain_test_period = [i],
                      cash = [i],
                      slippage = [i],
                      max_weight = [i],
                      min_weight = [i],
                      report_name = [i],
                      log_name = [i])

    # variables

    # for i in range

import pandas as pd
import datetime
import numpy as np
import math
import calendar
import concurrent
import multiprocessing
import concurrent.futures
import psycopg2
import streamlit as st
from psycopg2.pool import ThreadedConnectionPool

def get_date_range(df, start_date, end_date):
    df = df.set_index('date')
    df.index = pd.to_datetime(df.index, format='%Y-%m-%d')
    df.sort_index(inplace=True)
    df = df[start_date:end_date]
    df = df.reset_index()
    return df

def get_price_range(df, price_lower_limit, price_upper_limit):
    df = df[(df.buy_price >= price_lower_limit) & (df.buy_price <= price_upper_limit)]
    return df

def get_short_term_range(df, short_term_ret_lower, short_term_ret_upper):
    df = df[(df.short_term_look_return >= short_term_ret_lower) & (df.short_term_look_return <= short_term_ret_upper)]
    return df

def get_long_term_range(df, long_term_ret_lower, long_term_ret_upper):
    df = df[(df.long_term_look_return >= long_term_ret_lower) & (df.long_term_look_return <= long_term_ret_upper)]
    return df

def get_agv_vol_range(df, avg_daily_dollar_vol_lower, avg_daily_dollar_vol_upper):
    df = df[(df.avg_daily_volume_over_volume_lookback_period >= avg_daily_dollar_vol_lower) & (
                df.avg_daily_volume_over_volume_lookback_period <= avg_daily_dollar_vol_upper)]
    return df

def get_median_vol_range(df, median_daily_dollar_vol_lower, median_daily_dollar_vol_upper):
    df = df[(df.median_daily_volume_over_volume_lookback_period >= median_daily_dollar_vol_lower) & (
                df.median_daily_volume_over_volume_lookback_period <= median_daily_dollar_vol_upper)]
    return df

def get_dollar_vol_ratio_range(df, dollar_vol_ratio_lower, dollar_vol_ratio_upper):
    df = df[(df.dollar_volume_ratio >= dollar_vol_ratio_lower) & (df.dollar_volume_ratio <= dollar_vol_ratio_upper)]
    return df

def filter_onePeriod(dataframe,
                     start_date,
                     end_date,
                     price_lower_limit,
                     price_upper_limit,
                     short_term_ret_lower,
                     short_term_ret_upper,
                     long_term_ret_lower,
                     long_term_ret_upper,
                     avg_daily_dollar_vol_lower,
                     avg_daily_dollar_vol_upper,
                     median_daily_dollar_vol_lower,
                     median_daily_dollar_vol_upper,
                     dollar_vol_ratio_lower,
                     dollar_vol_ratio_upper):
    if len(dataframe) != 0:
        df = get_date_range(dataframe, start_date, end_date)

        if len(df) != 0:
            df = get_price_range(df, price_lower_limit, price_upper_limit)

            if len(df) != 0:
                df = get_short_term_range(df, short_term_ret_lower, short_term_ret_upper)

                if len(df) != 0:
                    df = get_long_term_range(df, long_term_ret_lower, long_term_ret_upper)

                    if len(df) != 0:
                        df = get_agv_vol_range(df, avg_daily_dollar_vol_lower, avg_daily_dollar_vol_upper)

                        if len(df) != 0:
                            df = get_median_vol_range(df, median_daily_dollar_vol_lower, median_daily_dollar_vol_upper)

                            if len(df) != 0:

                                df = get_dollar_vol_ratio_range(df, dollar_vol_ratio_lower, dollar_vol_ratio_upper)

                            else:
                                return False, None
                        else:
                            return False, None
                    else:
                        return False, None
                else:
                    return False, None
            else:
                return False, None
        else:
            return False, None
    else:
        return False, None
    return df


def get_indicators(df):
    if df.shape[0] == 0:
        trata = []
        trata.append("No Results Available")
        return trata
    else:
        table_results = {'total_transaction': df.shape[0],
                         'mean_cum_return_for_holding_period': df.cumulative_return_holdingPeriod.mean(),
                         'median_cum_return_for_holding_period': df.cumulative_return_holdingPeriod.median(),
                         'standard_dev_ret': df.cumulative_return_holdingPeriod.std()}
        df = df.sort_values('cumulative_return_holdingPeriod', ascending=False)
        ordered_ret = df['cumulative_return_holdingPeriod'].to_list()
        volume = df["avg_daily_volume_over_volume_lookback_period"].to_list()
        holding = df['actual_holding_period'].to_list()
        ret = sorted(ordered_ret, reverse=True)
        #volume = sorted(oredered_vol, reverse=True)
        n = math.floor(len(ret) * 10 / 100)
        if n!=0:
            return_cum = [ret[i * n:(i + 1) * n] for i in range((len(ret) + n - 1) // n)]
            volume_divided = [volume[i * n:(i + 1) * n] for i in range((len(ret) + n - 1) // n)]
            holding_divided = [holding[i * n:(i + 1) * n] for i in range((len(ret) + n - 1) // n)]
            table_results['mean_ret_top_10%_1'] = np.mean(return_cum[0])
            table_results['median_ret_top_10%_1'] = np.median(return_cum[0])
            table_results['mean_vol_top_10%_ret_1'] = np.mean(volume_divided[0])
            table_results['median_vol_top_10%_ret_1'] = np.median(volume_divided[0])
            table_results['mean_holding_top_10%_ret_1'] = np.mean(holding_divided[0])
            table_results['median_holding_top_10%_ret_1'] = np.median(holding_divided[0])

            table_results['mean_ret_top_10%_2'] = np.mean(return_cum[1])
            table_results['median_ret_top_10%_2'] = np.median(return_cum[1])
            table_results['mean_vol_top_10%_ret_2'] = np.mean(volume_divided[1])
            table_results['median_vol_top_10%_ret_2'] = np.median(volume_divided[1])
            table_results['mean_holding_top_10%_ret_2'] = np.mean(holding_divided[1])
            table_results['median_holding_top_10%_ret_2'] = np.median(holding_divided[1])

            table_results['mean_ret_top_10%_3'] = np.mean(return_cum[2])
            table_results['median_ret_top_10%_3'] = np.median(return_cum[2])
            table_results['mean_vol_top_10%_ret_3'] = np.mean(volume_divided[2])
            table_results['median_vol_top_10%_ret_3'] = np.median(volume_divided[2])
            table_results['mean_holding_top_10%_ret_3'] = np.mean(holding_divided[2])
            table_results['median_holding_top_10%_ret_3'] = np.median(holding_divided[2])

            table_results['mean_ret_top_10%_4'] = np.mean(return_cum[3])
            table_results['median_ret_top_10%_4'] = np.median(return_cum[3])
            table_results['mean_vol_top_10%_ret_4'] = np.mean(volume_divided[3])
            table_results['median_vol_top_10%_ret_4'] = np.median(volume_divided[3])
            table_results['mean_holding_top_10%_ret_4'] = np.mean(holding_divided[3])
            table_results['median_holding_top_10%_ret_4'] = np.median(holding_divided[3])

            table_results['mean_ret_top_10%_5'] = np.mean(return_cum[4])
            table_results['median_ret_top_10%_5'] = np.median(return_cum[4])
            table_results['mean_vol_top_10%_ret_5'] = np.mean(volume_divided[4])
            table_results['median_vol_top_10%_ret_5'] = np.median(volume_divided[4])
            table_results['mean_holding_top_10%_ret_5'] = np.mean(holding_divided[4])
            table_results['median_holding_top_10%_ret_5'] = np.median(holding_divided[4])

            table_results['mean_ret_top_10%_6'] = np.mean(return_cum[5])
            table_results['median_ret_top_10%_6'] = np.median(return_cum[5])
            table_results['mean_vol_top_10%_ret_6'] = np.mean(volume_divided[5])
            table_results['median_vol_top_10%_ret_6'] = np.median(volume_divided[5])
            table_results['mean_holding_top_10%_ret_6'] = np.mean(holding_divided[5])
            table_results['median_holding_top_10%_ret_6'] = np.median(holding_divided[5])

            table_results['mean_ret_top_10%_7'] = np.mean(return_cum[6])
            table_results['median_ret_top_10%_7'] = np.median(return_cum[6])
            table_results['mean_vol_top_10%_ret_7'] = np.mean(volume_divided[6])
            table_results['median_vol_top_10%_ret_7'] = np.median(volume_divided[6])
            table_results['mean_holding_top_10%_ret_7'] = np.mean(holding_divided[6])
            table_results['median_holding_top_10%_ret_7'] = np.median(holding_divided[6])

            table_results['mean_ret_top_10%_8'] = np.mean(return_cum[7])
            table_results['median_ret_top_10%_8'] = np.median(return_cum[7])
            table_results['mean_vol_top_10%_ret_8'] = np.mean(volume_divided[7])
            table_results['median_vol_top_10%_ret_8'] = np.median(volume_divided[7])
            table_results['mean_holding_top_10%_ret_8'] = np.mean(holding_divided[7])
            table_results['median_holding_top_10%_ret_8'] = np.median(holding_divided[7])

            table_results['mean_ret_top_10%_9'] = np.mean(return_cum[8])
            table_results['median_ret_top_10%_9'] = np.median(return_cum[8])
            table_results['mean_vol_top_10%_ret_9'] = np.mean(volume_divided[8])
            table_results['median_vol_top_10%_9'] = np.median(volume_divided[8])
            table_results['mean_holding_top_10%_ret_9'] = np.mean(holding_divided[8])
            table_results['median_holding_top_10%_ret_9'] = np.median(holding_divided[8])

            table_results['mean_ret_top_10%_10'] = np.mean(return_cum[9])
            table_results['median_ret_top_10%_10'] = np.median(return_cum[9])
            table_results['mean_vol_top_10%_ret_10'] = np.mean(volume_divided[9])
            table_results['median_vol_top_10%_ret_10'] = np.median(volume_divided[9])
            table_results['mean_holding_top_10%_ret_10'] = np.mean(holding_divided[9])
            table_results['median_holding_top_10%_ret_10'] = np.median(holding_divided[9])

            table_results['mean_ret_very_bottom'] = np.mean(ret[n * 10:])
            table_results['median_ret_very_bottom'] = np.median(return_cum[n * 10:])
            table_results['mean_vol_very_bottom_ret'] = np.mean(volume_divided[n * 10:])
            table_results['median_vol_very_bottom_ret'] = np.median(volume_divided[n * 10:])
            table_results['mean_holding_very_bottom'] = np.mean(holding_divided[n * 10:])
            table_results['median_holding_very_bottom'] = np.median(holding_divided[n * 10:])

            table_results['number_of_stocky_per_10%'] = n
            table_results = pd.DataFrame(table_results.items(), columns=['Indicators', 'values'])
        else:
            table_results['mean_ret_first_10_or_less'] = np.mean(ret)
            table_results['median_ret_first_10_or_less'] = np.median(ret)
            table_results['mean_vol_first_10_or_less_ret'] = np.mean(volume)
            table_results['median_vol_first_10_or_less_ret'] = np.median(volume)
            table_results['mean_holding_first_10_or_less_ret'] = np.mean(holding)
            table_results['median_holding_first_10_or_less_ret'] = np.median(holding)

            table_results = pd.DataFrame(table_results.items(), columns=['Indicators', 'values'])
        return table_results


def unique_selection_30(df):
    # helper functions
    # convert helper function
    def convert_helper(partitions_tuple):
        return tuple(map(pd.Timestamp, partitions_tuple))

    def date_partition_helper(start_date, end_date) -> list:
        # extract first year, month and last year, month
        begin_year = start_date.year
        end_year = end_date.year
        begin_month = start_date.month
        end_month = end_date.month

        # generate partitions
        result_partitions = []
        month_counter = begin_month
        for cur_year in range(begin_year, end_year + 1):
            if cur_year != end_year:
                while month_counter <= 12:
                    month_range = calendar.monthrange(cur_year, month_counter)
                    cur_begin_date = datetime.datetime(year=cur_year, month=month_counter, day=1)
                    cur_end_date = datetime.datetime(year=cur_year, month=month_counter, day=month_range[-1])
                    result_partitions.append((cur_begin_date, cur_end_date))
                    month_counter += 1
            else:
                while month_counter <=end_month:
                    month_range = calendar.monthrange(cur_year, month_counter)
                    cur_begin_date = datetime.datetime(year=cur_year, month=month_counter, day=1)
                    cur_end_date = datetime.datetime(year=cur_year, month=month_counter, day=month_range[-1])
                    result_partitions.append((cur_begin_date, cur_end_date))
                    month_counter += 1
            month_counter = 1

        return list(map(convert_helper, result_partitions))

    # multi index
    df = df.set_index(['date', 'stocks']).sort_index()

    # get date series partitions
    result_partitions = date_partition_helper(start_date=df.index.get_level_values(0)[0], end_date=df.index.get_level_values(0)[-1])

    # subset & concat
    result_dfs = []
    for start_condition, end_condition in result_partitions:
        cur_mask = (df.index.get_level_values(0) <= end_condition) & (df.index.get_level_values(0) >= start_condition)
        cur_df = df[cur_mask]
        cur_df = cur_df.reset_index()
        cur_df = cur_df.drop_duplicates(subset='stocks', keep='first', ignore_index=True)
        result_dfs.append(cur_df)
    result = pd.concat(result_dfs, ignore_index=True)

    return result

def month_distribution(df):
    # subset and add a month_year column
    data = df.copy()
    data = data[['date', 'cumulative_return_holdingPeriod']]
    def parse_single_date(pd_date):
        year = pd_date.year
        month = pd_date.month
        if month >= 10:
            return '{year}-{month}'.format(month=month,
                                    year=year)
        else:
            return '{year}-{month}'.format(month='0' + str(month),
                                    year=year)
    data['year_month'] = data['date'].apply(parse_single_date)

    # multiindex, group by, return concated result
    data = data.set_index(['year_month', 'date'])
    avg_ret = data.groupby(level=0).mean()
    trans_count = data.groupby(level=0).count()
    return_df = pd.concat([avg_ret, trans_count], axis=1)
    return_df.columns = ['Avg_return', 'Transactions']
    return_df = return_df.sort_index()

    return return_df

def get_future_daily_ret_multiple(symbols, dates, num_days, tcp):
    def get_future_daily_ret(symbol, date, num_days):
        conn = tcp.getconn()
        c = conn.cursor()
        c.execute("""select "adjClose" from "{symbol}" where date >= '{date}' limit {num_days};""".format(symbol=symbol, date=date, num_days=num_days + 1))
        adjClose = np.array([i[0] for i in c.fetchall()])
        tcp.putconn(conn)
        return np.diff(adjClose) / adjClose[:-1]

    args = [(cur_symbol, cur_date, num_days) for cur_symbol, cur_date in zip(symbols, dates)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        result = pool.map(lambda p: get_future_daily_ret(*p), args)

    return result

def stop_loss(list_of_ret, stop_value, buying_adjusts):
    cumulative_rets = []
    max_prices = []
    min_prices = []
    actual_holdings = []
    stop_value = -stop_value
    for cur_ret, buying_adjust in zip(list_of_ret, buying_adjusts):
        cur_cumulative = np.cumprod((cur_ret + 1)) - 1
        occurrence_series = np.where(cur_cumulative < stop_value)
        # if not stop
        if occurrence_series[0].size != 0:
            if occurrence_series[0][0] == 0:
                cur_cumulative = np.array([cur_cumulative[0]])
            else:
                cur_cumulative = cur_cumulative[:(occurrence_series[0][0] + 1)]
        price_series = buying_adjust * (cur_cumulative + 1)
        cumulative_rets.append(cur_cumulative[-1])
        max_prices.append(np.max(price_series))
        min_prices.append(np.min(price_series))
        actual_holdings.append(len(price_series))

    return {'cum_rets': cumulative_rets, 'max_prices': max_prices, 'min_prices': min_prices, 'actual_holdings': actual_holdings}


def after_buy(args):
    zio = args[0]
    range_test = args[1]
    stop_loss_test_period = args[2]/-100
    stop_gain_test_period = args[3]/100
    dropdown_allow_in_gain = args[4]/-100
    slippage = args[5]/100

    adjClose = zio.columns.get_loc("adjClose")
    zio.iloc[0, adjClose] = zio.iloc[0, adjClose] * (1 + slippage)

    zio = zio.set_index("date")
    zio.index = pd.to_datetime(zio.index, format="%Y/%m/%d")
    zio["ret"] = zio["adjClose"] / zio["adjClose"].shift(1) - 1
    zio["action"] = 0  # 0= hold, 1=buy, -1= sell
    future_observation = len(zio)
    action = zio.columns.get_loc("action")

    if (future_observation == 0):  # exception for symbol with one observation. If you make the return you get 0 length
        zio = zio.copy()
    elif future_observation == 1:
        zio.iloc[0, action] = 1  # set buy first day available

    elif future_observation > 1:
        zio.iloc[0, action] = 1  # set buy first day available
        if future_observation < range_test:

            range_test = future_observation  # set the new upper bound
            if future_observation <= range_test:
                for i in range(future_observation):
                    tot_ret = ((zio["ret"] + 1).cumprod(skipna=True) - 1)
                    tot_ret = tot_ret.tolist()
                    if (i < range_test and i != 0) and tot_ret[
                        i
                    ] < stop_loss_test_period:
                        zio.iloc[i, action] = -1
                        break

                    elif (i == range_test) and tot_ret[i] < stop_gain_test_period:
                        zio.iloc[i, action] = -1
                        break
        else:
            for g in range(future_observation):
                tot_ret = ((zio["ret"] + 1).cumprod(skipna=True) - 1)
                tot_ret = tot_ret.tolist()

                if (g < range_test and g != 0) and tot_ret[
                    g
                ] < stop_loss_test_period:
                    zio.iloc[g, action] = -1

                    break

                elif (g == range_test) and tot_ret[g] < stop_gain_test_period:
                    zio.iloc[g, action] = -1
                    break

                elif g >= range_test + 1:
                    if g == future_observation:
                        zio.iloc[
                            g, action
                        ] = "Position still open in profit after the range period set."

                    else:
                        pt = zio["adjClose"][g]
                        pt_max = zio["adjClose"][range_test: g + 1].max()
                        drop_from_max_price = (pt - pt_max) / pt_max

                        if drop_from_max_price <= dropdown_allow_in_gain:
                            zio.iloc[g, action] = -1
                            break

        sell_day = zio[zio["action"] == -1].index.date


        if sell_day.size == 0:
            zio["ret"] = zio["adjClose"] / zio["adjClose"].shift(1) - 1
            zio["cumulative_return"] = ((zio["ret"] + 1).cumprod(skipna=True) - 1)
            ret_gain = zio.iloc[future_observation - 1, :]["cumulative_return"]
        else:
            zio = zio.loc[: sell_day[0]]
            adjClose = zio.columns.get_loc("adjClose")
            zio.iloc[-1, adjClose] = zio.iloc[-1, adjClose] * (1 - slippage)
            zio["ret"] = zio["adjClose"] / zio["adjClose"].shift(1) - 1
            zio["cumulative_return"] = ((zio["ret"] + 1).cumprod(skipna=True) - 1)
            ret_gain = zio[zio["action"] == -1]["cumulative_return"][0]

    info_after_buy = {}
    info_after_buy['cum_rets'] = ret_gain  # (zio.iloc[-1, adjClose]/zio.iloc[0, adjClose]) -1
    info_after_buy['max_prices'] = max(zio['adjClose'])
    info_after_buy['min_prices'] = min(zio['adjClose'])
    info_after_buy['actual_holdings'] = len(zio)
    return info_after_buy


def after_buy_multiple(symbols, dates, tcp, range_test=45, stop_loss_test_period=-0.40, stop_gain_test_period=0.50,
                       dropdown_allow_in_gain=-0.25, slippage=0.2):
    # helper function
    # get single symbols' df
    def get_single(symbol, date):
        conn = tcp.getconn()
        sql_query = """select * from "{symbol}" where date >= '{date}';""".format(symbol=symbol, date=date)
        result = pd.read_sql_query(sql_query, conn)
        tcp.putconn(conn)

        return result

    # use multithread to retrieve data
    args = [(cur_symbol, cur_date) for cur_symbol, cur_date in zip(symbols, dates)]
    with concurrent.futures.ThreadPoolExecutor(10) as pool:
        results = list(pool.map(lambda p: get_single(*p), args))

    # use multiprocess to evaluate
    args = [(cur_df, range_test, stop_loss_test_period, stop_gain_test_period, dropdown_allow_in_gain, slippage) for cur_df in results]
    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as pool:
        results = list(pool.map(after_buy, args))

    return results

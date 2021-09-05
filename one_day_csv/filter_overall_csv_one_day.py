# dependencies
import psycopg2
import numpy as np
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay


def init_connection():
    return psycopg2.connect(dbname="jiijcknc", host="plain-legume.db.elephantsql.com", port=5432, user="jiijcknc",
                            password='C-o8mRiEn9yPzF5VONJh9sv8WAyQ9Bhg')


def get_all_symbols_list(conn):
    tot_symbol = pd.read_sql_query("SELECT * FROM tot_symbols", conn)
    symbols_tot = tot_symbol["symbol"].to_list()
    ex_list = pd.read_sql_query("SELECT * FROM exceptions", conn)
    symbols_ex = ex_list["symbol_ex"].to_list()
    symbols = list(set(symbols_tot) - set(symbols_ex))

    return sorted(symbols)


def get_data_single(symbol, conn):
    template = """select * from "{symbol}";"""
    return pd.read_sql_query(template.format(symbol=symbol), conn)


# return date price
def price_at_date(symbol, date, conn):
    template = """select * from "{symbol}" where date = '{date}';"""
    result = pd.read_sql_query(template.format(symbol=symbol, date=date), conn)

    if result.empty:
        return np.NAN

    return result["adjClose"][0]


# return num of days before
def num_days_before(df, date):
    return len(df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()])


# return num of days after
def num_days_after(df, date):
    return len(df.index[df["date"] > datetime.strptime(date, "%Y-%m-%d").date()])


# return lookback cumulative returns
def lookback_cum_ret(df, date, look_back_days):
    # retrieve subset
    subset = df.iloc[
             df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()], :
             ][-look_back_days:]
    # calculate the daily returns
    daily_return = subset["adjClose"].pct_change(1)

    return ((daily_return + 1).cumprod(skipna=True) - 1).iloc[-1]


# return the average volume
def lookback_avg_dollarVol(df, date, look_back_days):
    # retrieve subset
    subset = df.iloc[
             df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()], :
             ][-look_back_days:]

    # calculate dollar volume
    dollarVol = subset["adjClose"] * subset["volume"]

    return dollarVol.mean()


# return the median volume
def lookback_median_dollarVol(df, date, look_back_days):
    # retrieve subset
    subset = df.iloc[
             df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()], :
             ][-look_back_days:]

    # calculate dollar volume
    dollarVol = subset["adjClose"] * subset["volume"]

    return dollarVol.median()


# check for single symbol
def scanning_onePeriod(
        symbol,
        date,
        holding_period,
        price_lower_limit,
        price_upper_limit,
        short_term_ret_lookback,
        short_term_ret_lower,
        short_term_ret_upper,
        long_term_ret_lookback,
        long_term_ret_lower,
        long_term_ret_upper,
        vol_lookback,
        avg_daily_dollar_vol_lower,
        avg_daily_dollar_vol_upper,
        median_daily_dollar_vol_lower,
        median_daily_dollar_vol_upper,
        dollar_vol_ratio_short,
        dollar_vol_ratio_long,
        dollar_vol_ratio_lower,
        dollar_vol_ratio_upper,
        conn,
):
    # price limit check
    date_price = price_at_date(symbol, date, conn)
    if date_price is not None:
        if price_lower_limit <= date_price <= price_upper_limit:
            # if the date is available, get the whole dataframe
            data = get_data_single(symbol, conn)
            # number of days before condition
            max_lookback = max(
                short_term_ret_lookback,
                long_term_ret_lookback,
                vol_lookback,
                dollar_vol_ratio_short,
                dollar_vol_ratio_long,
            )
            days_before = num_days_before(data, date)
            if days_before > max_lookback:
                # number of days after condition
                days_after = num_days_after(data, date)
                if days_after > holding_period:
                    # short term return condition
                    short_term_ret = lookback_cum_ret(data, date, short_term_ret_lookback)
                    if short_term_ret_lower <= short_term_ret <= short_term_ret_upper:
                        # long term return condition
                        long_term_ret = lookback_cum_ret(data, date, long_term_ret_lookback)
                        if long_term_ret_lower <= long_term_ret <= long_term_ret_upper:
                            # average volume condition
                            avg_daily_dollar_vol = lookback_avg_dollarVol(data, date, vol_lookback)
                            if avg_daily_dollar_vol_lower <= avg_daily_dollar_vol <= avg_daily_dollar_vol_upper:
                                # median volume condition
                                median_daily_dollar_vol = lookback_median_dollarVol(data, date, vol_lookback)
                                if median_daily_dollar_vol_lower <= median_daily_dollar_vol <= median_daily_dollar_vol_upper:
                                    # dollar volume ratio condition
                                    dollar_vol_short = lookback_median_dollarVol(data, date, dollar_vol_ratio_short)
                                    dollar_vol_long = lookback_median_dollarVol(data, date, dollar_vol_ratio_long)
                                    if dollar_vol_long != 0:
                                        dollar_vol_ratio = dollar_vol_short / dollar_vol_long
                                        if dollar_vol_ratio_lower <= dollar_vol_ratio <= dollar_vol_ratio_upper:
                                            return (
                                                True,
                                                data.iloc[
                                                    data.index[
                                                        data["date"]
                                                        >= datetime.strptime(
                                                            date, "%Y-%m-%d"
                                                        ).date()
                                                        ]
                                                ],
                                                {
                                                    "long_term_look_return": long_term_ret,
                                                    "short_term_look_return": short_term_ret,
                                                    "avg_daily_volume_over_volume_lookback_period": avg_daily_dollar_vol,
                                                    "median_daily_volume_over_volume_lookback_period": median_daily_dollar_vol,
                                                    "dollar_volume_ratio": dollar_vol_ratio,
                                                },
                                            )
                                        else:
                                            return False, None, None
                                    else:
                                        return False, None, None
                                else:
                                    return False, None, None
                            else:
                                return False, None, None
                        else:
                            return False, None, None
                    else:
                        return False, None, None
                else:
                    return False, None, None
            else:
                return False, None, None
        else:
            return False, None, None
    else:
        return False, None, None


def one_day_screening(stocks_dictionary, candidates_measurements, period=30):
    all_dictionary = []
    if len(stocks_dictionary) == 0:
        pass
    else:
        stocks_list = list(stocks_dictionary.keys())
        for stock in stocks_list:
            row_dictionary = {}
            df = stocks_dictionary[stock]
            if df.shape[0] < period:
                hold_period = (df.shape[0]) - 1
            else:
                hold_period = period

            df = df.set_index('date')
            df.index = pd.to_datetime(df.index, format='%Y/%m/%d')
            df["ret"] = df["adjClose"] / df["adjClose"].shift(1) - 1
            df["cumulative_return"] = ((df["ret"] + 1).cumprod(skipna=True) - 1)
            df = df.reset_index()

            date = df.columns.get_loc('date')
            position = 'buy'
            date = df.iloc[0, date]
            price = df.columns.get_loc('adjClose')
            cum_ret = df.columns.get_loc('cumulative_return')

            buy_adjClose = df.iloc[0, price]

            price_after_holding = df.iloc[hold_period, price]
            cum_ret_period = df.iloc[hold_period, cum_ret]
            min_max_price = df.iloc[0:hold_period, price]

            row_dictionary['stock'] = stock
            row_dictionary['date'] = str(date)
            row_dictionary['position'] = position
            row_dictionary['buy_adjClose'] = buy_adjClose
            s = f"adjClose_{period}_days"
            row_dictionary[s] = price_after_holding
            s = f"cum_ret_{period}_days"
            row_dictionary[s] = cum_ret_period

            row_dictionary['long_term_look_return'] = candidates_measurements[stock]['long_term_look_return']
            row_dictionary['short_term_look_return'] = candidates_measurements[stock]['short_term_look_return']
            row_dictionary['avg_daily_volume_over_volume_lookback_period'] = candidates_measurements[stock][
                'avg_daily_volume_over_volume_lookback_period']
            row_dictionary['median_daily_volume_over_volume_lookback_period'] = candidates_measurements[stock][
                'median_daily_volume_over_volume_lookback_period']
            row_dictionary['dollar_volume_ratio'] = candidates_measurements[stock]['dollar_volume_ratio']

            row_dictionary['min_price_during_holding_period'] = min_max_price.min()
            row_dictionary['max_price_during_holding_period'] = min_max_price.max()
            all_dictionary.append(row_dictionary)

    return all_dictionary

def organize_outputs_daily(total_outputs):
    col_names = ['stocks',
                 'date',
                 'position',
                 'buy_price',
                 'adjClose_after_holdingPeriod',
                 'long_term_look_return',
                 'short_term_look_return',
                 'avg_daily_volume_over_volume_lookback_period',
                 'median_daily_volume_over_volume_lookback_period',
                 'dollar_volume_ratio',
                 'cumulative_return_holdingPeriod',
                 'min_price_during_holding_period',
                 'max_price_during_holding_period']

    col_names2 = ['stock',
                  'date',
                  'position',
                  'buy_adjClose',
                  'adjClose_30_days',
                  'long_term_look_return',
                  'short_term_look_return',
                  'avg_daily_volume_over_volume_lookback_period',
                  'median_daily_volume_over_volume_lookback_period',
                  'dollar_volume_ratio',
                  'cum_ret_30_days',
                  'min_price_during_holding_period',
                  'max_price_during_holding_period']

    output_df = pd.DataFrame(columns=col_names2)

    for cur_date in list(total_outputs.keys()):
        temp1 = total_outputs[cur_date]
        for cur_rec in temp1:
            cur_rec = pd.Series(cur_rec)
            output_df = output_df.append(cur_rec, ignore_index=True)

    output_df = output_df[col_names2]
    output_df.columns = col_names

    return output_df

if __name__ == '__main__':
    # connection
    conn = init_connection()
    all_symbols = get_all_symbols_list(conn)

    # parameters
    start_date = '2018-01-01'
    end_date = '2018-02-01'
    holding_period = 30
    price_lower_limit = 0.0
    price_upper_limit = 10.0
    short_term_ret_lookback = 10
    short_term_ret_lower = 0.0
    short_term_ret_upper = 0.5
    long_term_ret_lookback = 120
    long_term_ret_lower = 0.0
    long_term_ret_upper = 1.0
    vol_lookback = 30
    avg_daily_dollar_vol_lower = 0.0
    avg_daily_dollar_vol_upper = 100000.0
    median_daily_volume_lower = 0.0
    median_daily_volume_upper = 100000.0
    dollar_vol_ratio_short = 10
    dollar_vol_ratio_long = 20
    dollar_vol_ratio_lower = 3
    dollar_vol_ratio_upper = 100

    # downloading
    # generate date series
    us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    date_series = list(pd.date_range(start=start_date, end=end_date, freq=us_bd))
    date_series = [i.strftime("%Y-%m-%d") for i in date_series]

    # loop for all days
    total_result_symbols = {}
    total_result_obs = {}
    for cur_date in tqdm(date_series, desc='Runnuing on dates...'):
        candidates_df = {}
        candidates_measurements = {}
        for symbol in tqdm(all_symbols, desc='Running on symbols...'):
            flag, df, obs = scanning_onePeriod(symbol=symbol,
                                               date=cur_date,
                                               holding_period=holding_period,
                                               price_lower_limit=price_lower_limit,
                                               price_upper_limit=price_upper_limit,
                                               short_term_ret_lookback=short_term_ret_lookback,
                                               short_term_ret_lower=short_term_ret_lower,
                                               short_term_ret_upper=short_term_ret_upper,
                                               long_term_ret_lookback=long_term_ret_lookback,
                                               long_term_ret_lower=long_term_ret_lower,
                                               long_term_ret_upper=long_term_ret_upper,
                                               vol_lookback=vol_lookback,
                                               avg_daily_dollar_vol_lower=avg_daily_dollar_vol_lower,
                                               avg_daily_dollar_vol_upper=avg_daily_dollar_vol_upper,
                                               median_daily_dollar_vol_lower=median_daily_volume_lower,
                                               median_daily_dollar_vol_upper=median_daily_volume_upper,
                                               dollar_vol_ratio_short=dollar_vol_ratio_short,
                                               dollar_vol_ratio_long=dollar_vol_ratio_long,
                                               dollar_vol_ratio_lower=dollar_vol_ratio_lower,
                                               dollar_vol_ratio_upper=dollar_vol_ratio_upper,
                                               conn=conn)
            if flag:
                candidates_df[symbol] = df
                candidates_measurements[symbol] = obs
        total_result_symbols[cur_date] = candidates_df
        total_result_obs[cur_date] = candidates_measurements

    # strategy
    total_outputs = {
        cur_date: one_day_screening(
            total_result_symbols[cur_date],
            total_result_obs[cur_date],
            period=holding_period,
        )
        for cur_date in tqdm(date_series, desc='Runnuing on strategy...')
    }

    total_df = organize_outputs_daily(total_outputs)

    # save
    total_df.to_csv('Overall.csv')

    conn.close()

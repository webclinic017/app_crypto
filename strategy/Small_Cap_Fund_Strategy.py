# Small_Cap_Fund_Strategy.py
# small cap fun strategy, reference: https://docs.google.com/document/d/16GjfRYZMCynFYt_mMRphvCIEu_A6Y8gBaPhOj9lpn2E/edit


import pandas as pd
import psycopg2
import streamlit as st
from datetime import datetime
from utilities.DB_connection import run_query_pandas


# get data for single symbol
@st.cache(
    hash_funcs={psycopg2.extensions.connection: id, "_thread.RLock": id},
    show_spinner=False,
)
def _get_data_single(symbol, conn):
    template = """select * from "{symbol}";"""
    return run_query_pandas(template.format(symbol=symbol), conn)


# check if the symbol is available on the observing date
@st.cache(
    hash_funcs={psycopg2.extensions.connection: id, "_thread.RLock": id},
    show_spinner=False,
)
def _checkAvailable_date(symbol, date, conn, price_lower_limit, price_upper_limit):
    template = """select * from "{symbol}" where date = '{date}';"""
    result = run_query_pandas(template.format(symbol=symbol, date=date), conn)

    if result.empty:
        return False
    price = result["adjClose"][0]

    return price_upper_limit >= price >= price_lower_limit


# check if number of dates before observing date satisfy the condition
@st.cache(show_spinner=False)
def _check_num_day_before(df, date, limit):
    before_length = len(
        df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()]
    )
    return before_length >= limit


# check if number of dates behind observing date satisfy the condition
@st.cache(show_spinner=False)
def _check_num_day_after(df, date, limit):
    after_length = len(
        df.index[df["date"] > datetime.strptime(date, "%Y-%m-%d").date()]
    )
    return after_length >= limit


# check if number of (volume == 0) is less than tolerance
@st.cache(show_spinner=False)
def _check_zeroVol_percent(
    df, date, before_day_limit, after_day_limit, percent_tolerance
):
    # check before
    before_index = df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()][
        -before_day_limit:
    ]
    before_zero_vol_num = (df.iloc[before_index, :]["volume"] == 0).sum()

    # check after
    after_index = df.index[df["date"] > datetime.strptime(date, "%Y-%m-%d").date()][
        :after_day_limit
    ]
    after_zero_vol_num = (df.iloc[after_index, :]["volume"] == 0).sum()

    return (
        (before_zero_vol_num + after_zero_vol_num)
        / (before_day_limit + after_day_limit)
    ) <= percent_tolerance


# check if average volume is above limit
@st.cache(show_spinner=False)
def _check_volAverage(df, date, limit, look_back_days):
    # retrieve subset
    subset = df.iloc[
        df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()], :
    ][-look_back_days:]
    # calculate the average volume
    average_vol = subset["volume"].mean()

    return average_vol < limit


# check if cumulative return is above limit
@st.cache(show_spinner=False)
def _check_cumulativeRet(df, date, limit, look_back_days):
    # retrieve subset
    subset = df.iloc[
        df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()], :
    ][-look_back_days:]
    # calculate the daily returns
    daily_return = subset["adjClose"].pct_change(1)

    # cumulative return
    cum_return = (daily_return + 1).cumprod(skipna=True) - 1

    return (cum_return > limit).any()


# TODO: x days short-term vol is greater than y days long-term vol for z percent

# check if the a stock satisfy all conditions
# test symbols: AABB
@st.cache(
    hash_funcs={psycopg2.extensions.connection: id, "_thread.RLock": id},
    show_spinner=False,
)
def check_single_symbol(
    symbol,
    price_lower_limit,
    price_upper_limit,
    observing_date,
    before_day_limit,
    after_day_limit,
    cumulative_limit,
    volAverage_limit,
    void_vol_percent_tolerance,
    conn,
    return_data=False,
):
    # check if the stock available on observing date
    if _checkAvailable_date(
        symbol=symbol,
        date=observing_date,
        conn=conn,
        price_upper_limit=price_upper_limit,
        price_lower_limit=price_lower_limit,
    ):

        # get the data of small stock
        data = _get_data_single(symbol=symbol, conn=conn)
        # check before date limit and after date limit
        if (
            _check_num_day_before(df=data, date=observing_date, limit=before_day_limit)
            and _check_num_day_after(
                df=data, date=observing_date, limit=after_day_limit
            )
            and _check_zeroVol_percent(
                df=data,
                date=observing_date,
                before_day_limit=before_day_limit,
                after_day_limit=after_day_limit,
                percent_tolerance=void_vol_percent_tolerance,
            )
        ):
            if _check_cumulativeRet(
                df=data,
                date=observing_date,
                limit=cumulative_limit,
                look_back_days=before_day_limit,
            ) and _check_volAverage(
                df=data,
                date=observing_date,
                limit=volAverage_limit,
                look_back_days=before_day_limit,
            ):
                if return_data:
                    return (
                        True,
                        data.iloc[
                            data.index[
                                data["date"]
                                >= datetime.strptime(observing_date, "%Y-%m-%d").date()
                            ],
                            :,
                        ],
                    )
                else:
                    return True
            else:
                if return_data:
                    return False, None
                else:
                    return False
        else:
            if return_data:
                return False, None
            else:
                return False
    else:
        if return_data:
            return False, None
        else:
            return False


@st.cache
def after_buy(
    zio,
    range_test=45,
    stop_loss_test_period=-0.40,
    stop_gain_test_period=0.50,
    dropdown_allow_in_gain=-0.25,
):
    """
    Parameters
    ----------
    zio = dataframe
    range_test = test holding period, 45 day default
    stop_loss_test_period = lost allow in test period, - 40% default
    stop_gain_test_period = gain resistance to keep ih holding, 50% deafault
    future_observation= how many days after the purchase do we wnat to look at? by default is the last day available of the dataframe
    drowdown_allow_in_gain = range_test onward, if the stock is ever down xxxxx from the high price it hits any day from 330pm EST to 4pm EST on day 46 or later, sell all of it.
    Returns
    -------
    """

    return_str = []
    zio = zio.set_index("date")
    zio.index = pd.to_datetime(zio.index, format="%Y/%m/%d")
    zio["ret"] = zio["adjClose"] / zio["adjClose"].shift(1) - 1
    zio["action"] = 0  # 0= hold, 1=buy, -1= sell
    zio = zio[
        zio["ret"].notna()
    ]  # i don't have to consider return missing values (first value)
    future_observation = len(zio)
    zio["cumulative_return"] = zio["ret"].cumsum()
    action = zio.columns.get_loc("action")
    if (
        future_observation == 0
    ):  # exception for symbol with one observation. If you make the return you get 0 length
        return_str.append("Not enough data available.\n")  # TODO
    elif future_observation == 1:
        zio.iloc[0, action] = 1  # set buy first day available
        buy_day = zio[zio["action"] == 1].index.date
        return_str.append(f"Bought on {buy_day[0]}.\n")  # TODO
        return_str.append("Symbol just bought.\n")  # TODO
    elif future_observation > 1:
        zio.iloc[0, action] = 1  # set buy first day available
        if future_observation < range_test:
            return_str.append(
                f"Data available are less than in the set {range_test}test period.\n"
            )  # TODO
            return_str.append(f"The analysis might be incomplete.\n")
            range_test = future_observation  # set the new upper bound
            if future_observation <= range_test:
                for i in range(future_observation):
                    tot_ret = zio["ret"].cumsum(skipna=True)
                    tot_ret = tot_ret.tolist()
                    if (i < range_test and i != 0) and tot_ret[
                        i
                    ] < stop_loss_test_period:
                        zio.iloc[i, action] = -1
                        return_str.append(
                            f"The price dropped of {stop_loss_test_period * 100}% in {range_test}th days or less.\n"
                        )  # TODO
                        break

                    elif (i == range_test) and tot_ret[i] < stop_gain_test_period:
                        return_str.append(
                            f"The price didn't rise of {stop_gain_test_period * 100}%  at the {range_test + 1}th day.\n"
                        )
                        zio.iloc[i, action] = -1
                        break

        else:

            for g in range(future_observation):
                tot_ret = zio["ret"].cumsum(skipna=True)
                tot_ret = tot_ret.tolist()

                if (g < range_test and g != 0) and tot_ret[
                    g
                ] < stop_loss_test_period:  # and tot_ret[i] < stop_loss_test_period:
                    zio.iloc[g, action] = -1
                    return_str.append(
                        f"Price dropped of {stop_loss_test_period * 100}% in {range_test}th days or less.\n"
                    )  # TODO
                    break

                elif (g == range_test) and tot_ret[g] < stop_gain_test_period:
                    return_str.append(
                        f"Price didn't rise of {stop_gain_test_period * 100}%  at the {range_test + 1}th day.\n"
                    )
                    zio.iloc[g, action] = -1
                    break

                elif g >= range_test + 1:
                    if g == future_observation:
                        zio.iloc[
                            g, action
                        ] = "Position still open in profit after the range period set."

                    else:
                        pt = zio["adjClose"][g]
                        pt_max = zio["adjClose"][range_test + 1 : g + 1].max()
                        drop_from_max_price = (pt - pt_max) / pt_max
                        # return_str.append(f"This is gain {drop_from_max_price } ")

                        if drop_from_max_price <= dropdown_allow_in_gain:
                            zio.iloc[g, action] = -1
                            return_str.append(
                                f"I am out! Max price  after the {range_test + 1}th day is {pt_max}, it drop of {dropdown_allow_in_gain * 100}%, the price at closing {pt}.  "
                            )
                            break

        buy_day = zio[zio["action"] == 1].index.date
        sell_day = zio[zio["action"] == -1].index.date

        if sell_day.size == 0:
            return_str.append(
                f"Still holding it! The symbol have been bought on {buy_day[0]}  "
            )
            ret_gain = zio.iloc[future_observation - 1, :]["cumulative_return"]
            return_str.append(f"Return so far: { ret_gain*100}%  ")
        else:
            tot_holding_days = str(sell_day - buy_day)
            tot_holding_days = tot_holding_days.replace("[datetime.timedelta(days=", "")
            tot_holding_days = tot_holding_days.replace(")]", "")
            tot_holding_days = int(tot_holding_days)
            ret_gain = zio[zio["action"] == -1]["cumulative_return"][0]
            return_str.append(f"Bought on {buy_day[0]}.  ")
            return_str.append(f"Hold it until {sell_day[0]}.  ")
            return_str.append(
                f"Total days holding includes not trading days: {tot_holding_days}.  "
            )
            return_str.append(f"The return on investment is {ret_gain * 100}%.  ")
            zio = zio.loc[: sell_day[0]]

    return zio, return_str

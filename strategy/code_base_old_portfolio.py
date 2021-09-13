# # Small_Cap_Fund_Portfolio.py
# # portfolio strategy functions
#
# # dependencies
# import psycopg2
# import numpy as np
# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from utilities.DB_connection import run_query_pandas
# from quantstats.stats import sharpe, sortino, max_drawdown, volatility
#
#
# # get data for single symbol
# @st.cache(
#     hash_funcs={psycopg2.extensions.connection: id, "_thread.RLock": id},
#     show_spinner=False,
# )
# def get_data_single(symbol, conn):
#     template = """select * from "{symbol}";"""
#     return run_query_pandas(template.format(symbol=symbol), conn)
#
#
# # return date price
# @st.cache(
#     hash_funcs={psycopg2.extensions.connection: id, "_thread.RLock": id},
#     show_spinner=False,
# )
# def price_at_date(symbol, date, conn):
#     template = """select * from "{symbol}" where date = '{date}';"""
#     result = pd.read_sql_query(template.format(symbol=symbol, date=date), conn)
#
#     if result.empty:
#         return np.NAN
#
#     return result["adjClose"][0]
#
#
# # return num of days before
# @st.cache(show_spinner=False)
# def num_days_before(df, date):
#     return len(df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()])
#
#
# # return num of days after
# @st.cache(show_spinner=False)
# def num_days_after(df, date):
#     return len(df.index[df["date"] > datetime.strptime(date, "%Y-%m-%d").date()])
#
#
# # return lookback cumulative returns
# @st.cache(show_spinner=False)
# def lookback_cum_ret(df, date, look_back_days):
#     # retrieve subset
#     subset = df.iloc[
#              df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()], :
#              ][-look_back_days:]
#     # calculate the daily returns
#     daily_return = subset["adjClose"].pct_change(1)
#
#     return ((daily_return + 1).cumprod(skipna=True) - 1).iloc[-1]
#
#
# # return the average volume
# @st.cache(show_spinner=False)
# def lookback_avg_dollarVol(df, date, look_back_days):
#     # retrieve subset
#     subset = df.iloc[
#              df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()], :
#              ][-look_back_days:]
#
#     # calculate dollar volume
#     dollarVol = subset["adjClose"] * subset["volume"]
#
#     return dollarVol.mean()
#
#
# # return the median volume
# @st.cache(show_spinner=False)
# def lookback_median_dollarVol(df, date, look_back_days):
#     # retrieve subset
#     subset = df.iloc[
#              df.index[df["date"] < datetime.strptime(date, "%Y-%m-%d").date()], :
#              ][-look_back_days:]
#
#     # calculate dollar volume
#     dollarVol = subset["adjClose"] * subset["volume"]
#
#     return dollarVol.median()
#
#
# # check for single symbol
# @st.cache(
#     hash_funcs={psycopg2.extensions.connection: id, "_thread.RLock": id},
#     show_spinner=False,
# )
# def scanning_onePeriod(
#         symbol,
#         date,
#         holding_period,
#         price_lower_limit,
#         price_upper_limit,
#         short_term_ret_lookback,
#         short_term_ret_lower,
#         short_term_ret_upper,
#         long_term_ret_lookback,
#         long_term_ret_lower,
#         long_term_ret_upper,
#         vol_lookback,
#         avg_daily_dollar_vol_lower,
#         avg_daily_dollar_vol_upper,
#         median_daily_dollar_vol_lower,
#         median_daily_dollar_vol_upper,
#         dollar_vol_ratio_short,
#         dollar_vol_ratio_long,
#         dollar_vol_ratio_lower,
#         dollar_vol_ratio_upper,
#         conn,
# ):
#     # price limit check
#     date_price = price_at_date(symbol, date, conn)
#     if date_price is not None:
#         if price_lower_limit <= date_price <= price_upper_limit:
#             # if the date is available, get the whole dataframe
#             data = get_data_single(symbol, conn)
#             # number of days before condition
#             max_lookback = max(
#                 short_term_ret_lookback,
#                 long_term_ret_lookback,
#                 vol_lookback,
#                 dollar_vol_ratio_short,
#                 dollar_vol_ratio_long,
#             )
#             days_before = num_days_before(data, date)
#             if days_before > max_lookback:
#                 # number of days after condition
#                 days_after = num_days_after(data, date)
#                 if days_after > holding_period:
#                     # short term return condition
#                     short_term_ret = lookback_cum_ret(data, date, short_term_ret_lookback)
#                     if short_term_ret_lower <= short_term_ret <= short_term_ret_upper:
#                         # long term return condition
#                         long_term_ret = lookback_cum_ret(data, date, long_term_ret_lookback)
#                         if long_term_ret_lower <= long_term_ret <= long_term_ret_upper:
#                             # average volume condition
#                             avg_daily_dollar_vol = lookback_avg_dollarVol(data, date, vol_lookback)
#                             if avg_daily_dollar_vol_lower <= avg_daily_dollar_vol <= avg_daily_dollar_vol_upper:
#                                 # median volume condition
#                                 median_daily_dollar_vol = lookback_median_dollarVol(data, date, vol_lookback)
#                                 if median_daily_dollar_vol_lower <= median_daily_dollar_vol <= median_daily_dollar_vol_upper:
#                                     # dollar volume ratio condition
#                                     dollar_vol_short = lookback_median_dollarVol(data, date, dollar_vol_ratio_short)
#                                     dollar_vol_long = lookback_median_dollarVol(data, date, dollar_vol_ratio_long)
#                                     if dollar_vol_long != 0:
#                                         dollar_vol_ratio = dollar_vol_short / dollar_vol_long
#                                         if dollar_vol_ratio_lower <= dollar_vol_ratio <= dollar_vol_ratio_upper:
#                                             return (
#                                                 True,
#                                                 data.iloc[
#                                                     data.index[
#                                                         data["date"]
#                                                         >= datetime.strptime(
#                                                             date, "%Y-%m-%d"
#                                                         ).date()
#                                                         ]
#                                                 ],
#                                                 {
#                                                     "long_term_look_return": long_term_ret,
#                                                     "short_term_look_return": short_term_ret,
#                                                     "avg_daily_volume_over_volume_lookback_period": avg_daily_dollar_vol,
#                                                     "median_daily_volume_over_volume_lookback_period": median_daily_dollar_vol,
#                                                     "dollar_volume_ratio": dollar_vol_ratio,
#                                                 },
#                                             )
#                                         else:
#                                             return False, None, None
#                                     else:
#                                         return False, None, None
#                                 else:
#                                     return False, None, None
#                             else:
#                                 return False, None, None
#                         else:
#                             return False, None, None
#                     else:
#                         return False, None, None
#                 else:
#                     return False, None, None
#             else:
#                 return False, None, None
#         else:
#             return False, None, None
#     else:
#         return False, None, None
#
# # strategy
# @st.cache(show_spinner=False)
# def weights(list_stock_selected, max_weight=20, liquidity=None):
#     """
#     Parameters
#     ----------
#     list_stock_selectecd = return list with all the selected stocks from the screening
#     max_weight = set the max weight percentage for each stock
#     initial_investment = how much o you want to invest?
#     liquidity = set a certain amount of liquidity you want to keep in your portfolio
#     Returns dataframe
#     -------
#     """
#     return_str = []
#     max_weight = max_weight / 100
#     n_stocks = len(list_stock_selected)
#     if liquidity:
#         if liquidity <= 100:
#             return_str.append(f"You have set up {liquidity}% of liquidity in your portfolio")
#             liquidity = liquidity / 100
#             weight = [(1 - liquidity) / n_stocks for i in range(n_stocks)]
#             for i in range(len(weight)):
#                 if weight[i] > max_weight:
#                     weight[i] = max_weight
#         else:
#             return_str.append(f"Can't short sell those symbol. The portfolio hase been automatically rebalanced.")
#             liquidity = 100
#             liquidity = liquidity / 100
#             weight = [(1 - liquidity) / n_stocks for i in range(n_stocks)]
#             for i in range(len(weight)):
#                 if weight[i] > max_weight:
#                     weight[i] = max_weight
#         weight_sum = sum(weight)
#         if liquidity < abs(1 - weight_sum):
#             liquidity = abs(1 - weight_sum)
#     else:
#         return_str.append(f"Liquidity will automatically set up if necessary")
#         weight = [1 / n_stocks for i in range(n_stocks)]
#         for i in range(len(weight)):
#             if weight[i] > max_weight:
#                 weight[i] = max_weight
#         weight_sum = sum(weight)
#         liquidity = abs(1 - weight_sum)
#     dict_weight = {}
#     for i in range(len(weight)):
#         symbol = list_stock_selected[i]
#         z = weight[i]
#         dict_weight[symbol] = z
#     return dict_weight, liquidity, return_str
#
# @st.cache(show_spinner=False)
# def buy_function(list_stock_selected, weight_function, initial_investment, stocks_dictionary, candidates_measurements):
#     dictionary_stocks_weight = weight_function[0]
#     liquidity = weight_function[1]
#     weight_sum = sum(dictionary_stocks_weight.values()) + liquidity
#     number_stocks = len(dictionary_stocks_weight)
#     all_dictionary = []
#     for i in range(number_stocks):
#         row_dictionary = {'date': None, 'position': None, 'stocks': None,
#                           'weight': None, 'portfolio_value': None,
#                           'adjClose': None, 'daily_ret': None,
#                           'cumulative_return': None}
#
#         stock = list_stock_selected[i]
#         weight = dictionary_stocks_weight[stock]
#         schei = initial_investment * weight
#
#         df = stocks_dictionary[stock]
#         df = df.set_index('date')
#         df.index = pd.to_datetime(df.index, format='%Y/%m/%d')
#         df["ret"] = df["adjClose"] / df["adjClose"].shift(1) - 1
#         df["cumulative_return"] = ((df["ret"] + 1).cumprod(skipna=True) - 1)
#
#         df = df.reset_index()
#         price = df.columns.get_loc('adjClose')
#         daily_ret = df.columns.get_loc('ret')
#         cum_ret = df.columns.get_loc('cumulative_return')
#         date = df.columns.get_loc('date')
#         price = df.iloc[0, price]
#         daily_ret = df.iloc[0, daily_ret]
#         cum_ret = df.iloc[0, cum_ret]
#         date = str(df.iloc[0, date])
#         row_dictionary['stocks'] = stock
#         row_dictionary['weight'] = weight
#         row_dictionary['portfolio_value'] = schei
#         row_dictionary['adjClose'] = price
#         row_dictionary['daily_ret'] = daily_ret
#         row_dictionary['cumulative_return'] = cum_ret
#         row_dictionary['date'] = date
#         row_dictionary['long_term_look_return'] = candidates_measurements[stock]['long_term_look_return']
#         row_dictionary['short_term_look_return'] = candidates_measurements[stock]['short_term_look_return']
#         row_dictionary['avg_daily_volume_over_volume_lookback_period'] = candidates_measurements[stock]['avg_daily_volume_over_volume_lookback_period']
#         row_dictionary['median_daily_volume_over_volume_lookback_period'] = candidates_measurements[stock]['median_daily_volume_over_volume_lookback_period']
#         row_dictionary['dollar_volume_ratio'] = candidates_measurements[stock]['dollar_volume_ratio']
#         all_dictionary.append(row_dictionary)
#
#     all_dictionary = pd.DataFrame(all_dictionary)
#     port = {'stocks': ['Portfolio', 'Liquidity'], 'weight': [weight_sum, liquidity],
#             'portfolio_value': [initial_investment, liquidity * initial_investment], }
#     yo = pd.DataFrame(port)
#     df_new = pd.DataFrame(all_dictionary)
#
#     initial_port = pd.concat([yo, df_new], sort=False)
#     initial_port['position'] = 'Buy'
#     initial_port['date'] = initial_port['date'].to_list()[-1]
#     initial_port = initial_port[
#         ['stocks', 'portfolio_value', 'daily_ret', 'date', 'position', 'weight', 'adjClose', 'cumulative_return',
#          'long_term_look_return', 'short_term_look_return',
#          'avg_daily_volume_over_volume_lookback_period', 'median_daily_volume_over_volume_lookback_period',
#          'dollar_volume_ratio']]
#
#     return initial_port, dictionary_stocks_weight
#
# @st.cache(show_spinner=False)
# def hold_function(stocks_dictionary, initial_port,
#                   number_days_before_rebalance, candidates_measurements):  # val_investment, ,number_days_before_rebalance): number_days_before_rebalance):
#
#     number_days_before_rebalance = number_days_before_rebalance - 2
#     full_history_hold = pd.DataFrame()
#     for i in range(number_days_before_rebalance):
#         if i == 0:
#             portfolio = initial_port
#         val_investment = portfolio.columns.get_loc('portfolio_value')
#         val_investment = portfolio.iloc[:, val_investment].to_list()
#         list_stock_selected = portfolio.columns.get_loc('stocks')
#         list_stock_selected = portfolio.iloc[2:, list_stock_selected].to_list()
#
#         port_tot = val_investment[0]
#         port_sotcks = val_investment[2:]
#         liquidity = val_investment[1]
#
#         all_dictionary = []
#         val_investment = []
#         for za in range(len(list_stock_selected)):
#             row_dictionary = {'date': None, 'position': None, 'stocks': None,
#                               'weight': None, 'portfolio_value': None,
#                               'adjClose': None, 'daily_ret': None,
#                               'cumulative_return': None}
#
#             val_stock_before = port_sotcks[za]
#             stock = list_stock_selected[za]
#             df = stocks_dictionary[stock]
#             df = df.set_index('date')
#             df.index = pd.to_datetime(df.index, format='%Y/%m/%d')
#             df["ret"] = df["adjClose"] / df["adjClose"].shift(1) - 1
#             df["cumulative_return"] = ((df["ret"] + 1).cumprod(skipna=True) - 1)
#             df = df.reset_index()
#             price = df.columns.get_loc('adjClose')
#             daily_ret = df.columns.get_loc('ret')
#             cum_ret = df.columns.get_loc('cumulative_return')
#             date = df.columns.get_loc('date')
#             price = df.iloc[i + 1, price]
#             daily_ret = df.iloc[i + 1, daily_ret]
#             cum_ret = df.iloc[i + 1, cum_ret]
#             date = df.iloc[i + 1, date]
#             schei = val_stock_before + (val_stock_before * daily_ret)
#
#             row_dictionary['date'] = str(date)
#             row_dictionary['stocks'] = stock
#             row_dictionary['portfolio_value'] = schei
#             row_dictionary['adjClose'] = price
#             row_dictionary['daily_ret'] = daily_ret
#             row_dictionary['cumulative_return'] = cum_ret
#             row_dictionary['long_term_look_return'] = candidates_measurements[stock]['long_term_look_return']
#             row_dictionary['short_term_look_return'] = candidates_measurements[stock]['short_term_look_return']
#             row_dictionary['avg_daily_volume_over_volume_lookback_period'] = candidates_measurements[stock][
#                 'avg_daily_volume_over_volume_lookback_period']
#             row_dictionary['median_daily_volume_over_volume_lookback_period'] = candidates_measurements[stock][
#                 'median_daily_volume_over_volume_lookback_period']
#             row_dictionary['dollar_volume_ratio'] = candidates_measurements[stock]['dollar_volume_ratio']
#             all_dictionary.append(row_dictionary)
#             val_investment.append(schei)
#
#         all_dictionary = pd.DataFrame(all_dictionary)
#
#         port_rebalanced = all_dictionary.columns.get_loc('portfolio_value')
#         port_tot_2 = sum(all_dictionary.iloc[:, port_rebalanced].to_list()) + liquidity
#
#         quotients = []
#         val_investment.insert(0, liquidity)
#         for number in val_investment:
#             quotients.append(number / (port_tot_2))
#
#         ret_portfolio = (port_tot_2 / port_tot) - 1
#         quotients.insert(0, sum(quotients))
#
#         port = {'stocks': ['Portfolio', 'Liquidity'],
#                 'portfolio_value': [port_tot_2, liquidity], 'daily_ret': [ret_portfolio, None]}
#         yo = pd.DataFrame(port)
#         df_new = pd.DataFrame(all_dictionary)
#         portfolio = pd.concat([yo, df_new], sort=False)
#         portfolio['weight'] = quotients
#         portfolio['position'] = 'Hold'
#         portfolio['date'] = portfolio['date'].to_list()[-1]
#         full_history_hold = [full_history_hold, portfolio]
#         full_history_hold = pd.concat(full_history_hold, sort=False)
#
#     return full_history_hold, portfolio
#
# @st.cache(show_spinner=False)
# def sell_function(stocks_dictionary, portfolio, number_days_before_rebalance, candidates_measurements):
#     '''
#     :param stocks_dictionary: from stocks selection
#     :param portfolio: last portfolio from hold_function
#     :param number_days_before_rebalance: how any day at the rebalance
#     :return:
#     '''
#     val_investment = portfolio.columns.get_loc('portfolio_value')
#     val_investment = portfolio.iloc[:, val_investment].to_list()
#     list_stock_selected = portfolio.columns.get_loc('stocks')
#     list_stock_selected = portfolio.iloc[2:, list_stock_selected].to_list()
#
#     port_tot = val_investment[0]
#     port_sotcks = val_investment[2:]
#     liquidity = val_investment[1]
#
#     all_dictionary = []
#     val_investment = []
#     for za in range(len(list_stock_selected)):
#         row_dictionary = {'date': None, 'position': None, 'stocks': None,
#                           'weight': None, 'portfolio_value': None,
#                           'adjClose': None, 'daily_ret': None,
#                           'cumulative_return': None}
#
#         val_stock_before = port_sotcks[za]
#         stock = list_stock_selected[za]
#         # schei = value_portfolio * weight
#         df = stocks_dictionary[stock]
#         df = df.set_index('date')
#         df.index = pd.to_datetime(df.index, format='%Y/%m/%d')
#         df["ret"] = df["adjClose"] / df["adjClose"].shift(1) - 1
#         df["cumulative_return"] = ((df["ret"] + 1).cumprod(skipna=True) - 1)
#
#         df = df.reset_index()
#         price = df.columns.get_loc('adjClose')
#         daily_ret = df.columns.get_loc('ret')
#         cum_ret = df.columns.get_loc('cumulative_return')
#         date = df.columns.get_loc('date')
#         price = df.iloc[number_days_before_rebalance, price]
#         daily_ret = df.iloc[number_days_before_rebalance, daily_ret]
#         cum_ret = df.iloc[number_days_before_rebalance, cum_ret]
#         date = df.iloc[number_days_before_rebalance, date]
#         schei = val_stock_before + (val_stock_before * daily_ret)
#
#         row_dictionary['date'] = str(date)
#         row_dictionary['stocks'] = stock
#         # row_dictionary['weight'] = weight
#         row_dictionary['portfolio_value'] = schei
#         row_dictionary['adjClose'] = price
#         row_dictionary['daily_ret'] = daily_ret
#         row_dictionary['cumulative_return'] = cum_ret
#         row_dictionary['long_term_look_return'] = candidates_measurements[stock]['long_term_look_return']
#         row_dictionary['short_term_look_return'] = candidates_measurements[stock]['short_term_look_return']
#         row_dictionary['avg_daily_volume_over_volume_lookback_period'] = candidates_measurements[stock][
#             'avg_daily_volume_over_volume_lookback_period']
#         row_dictionary['median_daily_volume_over_volume_lookback_period'] = candidates_measurements[stock][
#             'median_daily_volume_over_volume_lookback_period']
#         row_dictionary['dollar_volume_ratio'] = candidates_measurements[stock]['dollar_volume_ratio']
#
#         all_dictionary.append(row_dictionary)
#         val_investment.append(schei)
#
#     all_dictionary = pd.DataFrame(all_dictionary)
#
#     port_rebalanced = all_dictionary.columns.get_loc('portfolio_value')
#     port_tot_2 = sum(all_dictionary.iloc[:, port_rebalanced].to_list()) + liquidity
#
#
#     quotients = []
#     val_investment.insert(0, liquidity)
#     for number in val_investment:
#         quotients.append(number / (port_tot_2))
#
#     ret_portfolio = (port_tot_2 / port_tot) - 1
#     quotients.insert(0, sum(quotients))
#
#     port = {'stocks': ['Portfolio', 'Liquidity'],
#             'portfolio_value': [port_tot_2, liquidity], 'daily_ret': [ret_portfolio, None]}
#     yo = pd.DataFrame(port)
#     df_new = pd.DataFrame(all_dictionary)
#     portfolio_sell = pd.concat([yo, df_new], sort=False)
#     portfolio_sell['weight'] = quotients
#     portfolio_sell['position'] = 'sell'
#     portfolio_sell['date'] = portfolio_sell['date'].to_list()[-1]
#
#     return portfolio_sell
#
# def portfolio(list_stock_selected, stocks_dictionary, candidates_measurements, max_weight=20, liquidity=None, initial_investment=1000,
#               number_days_before_rebalance=30):
#     weight_function = weights(list_stock_selected, max_weight, liquidity)
#     initial_port = buy_function(list_stock_selected, weight_function, initial_investment, stocks_dictionary,candidates_measurements)
#     portfolio = hold_function(stocks_dictionary, initial_port[0], number_days_before_rebalance, candidates_measurements)
#     sell = sell_function(stocks_dictionary, portfolio[1], number_days_before_rebalance, candidates_measurements)
#     overall_porfolio = pd.concat([initial_port[0], portfolio[0], sell], ignore_index=True)
#
#     info_df = overall_porfolio.copy()
#     portfolio_df = info_df[info_df['stocks'] == 'Portfolio']
#     portfolio_df = portfolio_df[portfolio_df['position'] != 'sell']
#     portfolio_df = portfolio_df.set_index('date')
#     portfolio_df.index = pd.to_datetime(portfolio_df.index, format='%Y/%m/%d')
#     portfolio_df["cumulative_ret"] = (portfolio_df["daily_ret"] + 1).cumprod(skipna=True) - 1
#     rata = portfolio_df.index.year.values
#     output_indicators = []
#     for i in np.unique(rata):
#         date = str(i)
#         middle_porfolio_df = portfolio_df[date]
#         output_indicators.append(f"#### Year considered: {date}")
#         output_indicators.append(f'''This is return cumulative: {(portfolio_df[date]["cumulative_ret"].to_list()[-1]*100):.4f}%''')
#         output_indicators.append(
#             f"This is SHARPE: {sharpe(returns=middle_porfolio_df.daily_ret, rf=0.0, periods=252 / 365, annualize=True, trading_year_days=252):.4f}\n")
#         output_indicators.append(
#             f"This is SORTINO RATIO: {sortino(returns=middle_porfolio_df.daily_ret, rf=0.0, periods=252 / 365, annualize=True, trading_year_days=252):.4f}\n")
#         output_indicators.append(
#             f"This is VOLATILITY: {volatility(returns=middle_porfolio_df.daily_ret, periods=252, annualize=True, trading_year_days=252):.4f}\n")
#         output_indicators.append(f"This is MAX DRAWDOWN: {max_drawdown(middle_porfolio_df.portfolio_value):.4f}\n")
#
#     return overall_porfolio, weight_function[2], output_indicators, portfolio_df

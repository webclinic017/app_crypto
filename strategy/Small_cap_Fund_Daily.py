
import pandas as pd


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

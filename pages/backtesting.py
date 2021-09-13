# backtesting.py
# backtesting page


import os
import math
import numpy as np
import pandas as pd
import streamlit as st
import datetime
import quantstats as qs
from datetime import date
from collections import defaultdict
from utilities.DB_connection import init_tcp
from utilities.common_data_retrieving import get_table_download_link, load_overall, load_dataset
from strategy.filter import get_indicators, filter_onePeriod, unique_selection_30, month_distribution, get_future_daily_ret_multiple, stop_loss, after_buy_multiple
from strategy.portfolio import backtester_engine


# call back function
def update_submitted():
    st.session_state.submitted = True


def small_cap_fund_daily_restricted(filter_csv, tcp):
    with st.form("Form.3:"):
        # start date and end date
        st.write('Date Range')
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                label="Start date",
                value=date(2016, 7, 12),
                min_value=date(2015, 5, 26),
                max_value=date(2021, 5, 17),
            )
        with col2:
            end_date = st.date_input(
                label="End date",
                value=date(2016, 7, 14),#date(2021, 2, 9),
                min_value=date(2015, 5, 26),
                max_value=date(2021, 5, 17)
            )
        start_date = start_date.strftime("%Y-%m-%d")  # start date
        end_date = end_date.strftime("%Y-%m-%d")  # end date
        # price range
        st.write('Price Range')
        col1, col2 = st.columns(2)
        with col1:
            price_lower_limit = st.number_input(
                label="Price lower bound($)", min_value=0.0, value=1.0
            )
        with col2:
            price_upper_limit = st.number_input(
                label="Price upper bound($)", value=6.0
            )
        # Return lookback
        st.write('Short Term Return Lookback')
        col11, col22 = st.columns(2)
        with col11:
            # short term ret range
            short_term_ret_lower = st.number_input(label='Lower bound(%)', value=10.0, min_value=-90.0, step=1.0,
                                                   key='short_lower')
            short_term_ret_lower /= 100
        with col22:
            short_term_ret_upper = st.number_input(label='Upper bound(%)', value=50.0, min_value=-90.0, step=1.0,
                                                   key='short_upper')
            short_term_ret_upper /= 100

        st.write('Long Term Return Lookback')
        col111, col222 = st.columns(2)
        with col111:
            # long term ret range
            long_term_ret_lower = st.number_input(label='Lower bound(%)', value=20.0, min_value=-90.0, step=1.0,
                                                  key='long_lower')
            long_term_ret_lower /= 100
        with col222:
            long_term_ret_upper = st.number_input(label='Upper bound(%)', value=100.0, min_value=-90.0, step=1.0,
                                                  key='long_upper')
            long_term_ret_upper /= 100

        # volume lookback
        st.write('Volume Lookback')
        col1111, col2222 = st.columns(2)
        with col1111:
            avg_daily_dollar_vol_lower = st.number_input(label='Average Daily Dollar Volume Lower Bound($)',
                                                         value=100000.0, min_value=0.0, step=0.01)
            median_daily_volume_lower = st.number_input(label='Median Daily Volume Lower Bound($)', value=100000.0,
                                                        min_value=0.0, step=0.01)
        with col2222:
            avg_daily_dollar_vol_upper = st.number_input(label='Average Daily Dollar Volume Upper Bound($)',
                                                         value=1000000.0, min_value=0.0, step=0.01)
            median_daily_volume_upper = st.number_input(label='Median Daily Volume Upper Bound($)', value=1000000.0,
                                                        min_value=0.0, step=0.01)
        # dollar volume ratio range
        st.write('Dollar Volume Ratio Range')
        col11111, col22222 = st.columns(2)
        with col11111:
            dollar_vol_ratio_lower = st.number_input(label='Ratio Lower Bound', min_value=0.0, value=3.0,
                                                     step=0.01)
        with col22222:
            dollar_vol_ratio_upper = st.number_input(label='Ratio Upper Bound', min_value=0.0, value=100.0, step=0.01)

        st.write('Trailing Stop loss')
        col111111, col222222 = st.columns(2)
        with col111111:
            range_test = st.number_input(label='Days Holding Test', min_value=1, value=45, step=1)
            dropdown_allow_in_gain = st.number_input(label='Stop Loss After-Test Period(%)', min_value=0, value=25)

        with col222222:
            stop_loss_test_period = st.number_input(label='Stop Loss Test Period (%)', min_value=1, value=40)
            stop_gain_test_period = st.number_input(label='Stop Gain Resistance Test Period(%)', min_value=1, value=50)

        slippage = st.number_input(label='Slippage (%)', min_value=0.0, value=2.0, step=0.01)

        unique_selection_30_bool = st.checkbox(label='Month unique selection', value=True)

        submitted = st.form_submit_button("Submit")



        if submitted:
            reserch = filter_onePeriod(dataframe=filter_csv, start_date=start_date, end_date=end_date,
                                       price_lower_limit=price_lower_limit, price_upper_limit=price_upper_limit,
                                       short_term_ret_lower=short_term_ret_lower,
                                       short_term_ret_upper=short_term_ret_upper,
                                       long_term_ret_lower=long_term_ret_lower, long_term_ret_upper=long_term_ret_upper,
                                       avg_daily_dollar_vol_lower=avg_daily_dollar_vol_lower,
                                       avg_daily_dollar_vol_upper=avg_daily_dollar_vol_upper,
                                       median_daily_dollar_vol_lower=median_daily_volume_lower,
                                       median_daily_dollar_vol_upper=median_daily_volume_upper,
                                       dollar_vol_ratio_lower=dollar_vol_ratio_lower,
                                       dollar_vol_ratio_upper=dollar_vol_ratio_upper)
            if  type(reserch) is tuple or reserch.empty:
                st.write('No Results Avaible')
            else:
                # if 30 days unique selection
                if unique_selection_30_bool:
                    reserch = unique_selection_30(reserch)

                # trailing stop loss
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

                # round result
                display_total_df = reserch.copy()
                display_total_df['buy_price'] = pd.Series(
                    ["{0:.2f}".format(val) for val in display_total_df['buy_price']], index=display_total_df.index)
                display_total_df['adjClose_after_holdingPeriod'] = pd.Series(
                    ["{0:.2f}".format(val) for val in display_total_df['adjClose_after_holdingPeriod']],
                    index=display_total_df.index)
                display_total_df['min_price_during_holding_period'] = pd.Series(
                    ["{0:.2f}".format(val) for val in display_total_df['min_price_during_holding_period']],
                    index=display_total_df.index)
                display_total_df['max_price_during_holding_period'] = pd.Series(
                    ["{0:.2f}".format(val) for val in display_total_df['max_price_during_holding_period']],
                    index=display_total_df.index)
                display_total_df['dollar_volume_ratio'] = pd.Series(
                    ["{0:.2f}".format(val) for val in display_total_df['dollar_volume_ratio']],
                    index=display_total_df.index)
                display_total_df['cumulative_return_holdingPeriod'] = pd.Series(
                    ["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in
                     display_total_df['cumulative_return_holdingPeriod']], index=display_total_df.index)
                display_total_df['long_term_look_return'] = pd.Series(
                    ["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in
                     display_total_df['long_term_look_return']], index=display_total_df.index)
                display_total_df['short_term_look_return'] = pd.Series(
                    ["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in
                     display_total_df['short_term_look_return']], index=display_total_df.index)
                display_total_df['avg_daily_volume_over_volume_lookback_period'] = pd.Series(
                    ["{}".format(int(val)) if not math.isnan(val) else "{}".format(val) for val in
                     display_total_df['avg_daily_volume_over_volume_lookback_period']], index=display_total_df.index)
                display_total_df['median_daily_volume_over_volume_lookback_period'] = pd.Series(
                    ["{}".format(int(val)) if not math.isnan(val) else "{}".format(val) for val in
                     display_total_df['median_daily_volume_over_volume_lookback_period']], index=display_total_df.index)

                # output
                st.write('## Output:')
                # performance
                st.write('Performance:')
                performance_expander = st.beta_expander(label='Performance')
                with performance_expander:
                    trat = get_indicators(reserch)
                    st.write('Performance:')
                    trat = trat.set_index('Indicators')
                    st.table(trat)
                # month distribution
                st.write('Month distribution table:')
                month_expander = st.beta_expander(label='Month distribution')
                with month_expander:
                    month_table = month_distribution(reserch)
                    st.table(month_table)
                st.write('Median Monthly Return: {}'.format(np.median(month_table['Avg_return'])))
                st.write('SD Monthly Return: {}'.format(np.std(month_table['Avg_return'])))
                st.markdown(get_table_download_link(month_table, 'month_distribution'), unsafe_allow_html=True)
                # month distribution plots
                st.write('Charts')
                chart_expander = st.beta_expander(label='Charts')
                with chart_expander:
                    generate_charts(month_table)
                # Overall result
                st.write('Overall Results:')
                table_expander = st.beta_expander(label='Overall Table')
                with table_expander:
                    st.table(display_total_df)
                st.write('### Download Overall.csv')
                st.write('Overall.csv')
                st.markdown(get_table_download_link(reserch, 'Overall'), unsafe_allow_html=True)
                st.write('Overall.csv (Rounded)')
                st.markdown(get_table_download_link(display_total_df, 'Overall'), unsafe_allow_html=True)

def generate_charts(month_table):
    st.write('Return line chart')
    st.line_chart(data=month_table['Avg_return'])
    st.write('Transcation line chart')
    st.line_chart(data=month_table['Transactions'])
    st.write('Return bar chart')
    st.bar_chart(data=month_table['Avg_return'])
    st.write('Transactions bar chart')
    st.bar_chart(data=month_table['Transactions'])



def portfolio(filter_csv, dataset, tcp):
    with st.form("Form.3:"):
        # start date and end date
        st.write('Date Range')
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                label="Start date",
                value=date(2016, 7, 12),
                min_value=date(2015, 5, 26),
                max_value=date(2021, 5, 17),
            )
        with col2:
            end_date = st.date_input(
                label="End date",
                value=date(2016, 7, 14),#date(2021, 2, 9),
                min_value=date(2015, 5, 26),
                max_value=date(2021, 5, 17)
            )
        start_date = start_date.strftime("%Y-%m-%d")  # start date
        end_date = end_date.strftime("%Y-%m-%d")  # end date
        # price range
        st.write('Price Range')
        col1, col2 = st.columns(2)
        with col1:
            price_lower_limit = st.number_input(
                label="Price lower bound($)", min_value=0.0, value=1.0
            )
        with col2:
            price_upper_limit = st.number_input(
                label="Price upper bound($)", value=6.0
            )
        # Return lookback
        st.write('Short Term Return Lookback')
        col11, col22 = st.columns(2)
        with col11:
            # short term ret range
            short_term_ret_lower = st.number_input(label='Lower bound(%)', value=10.0, min_value=-90.0, step=1.0,
                                                   key='short_lower')
            short_term_ret_lower /= 100
        with col22:
            short_term_ret_upper = st.number_input(label='Upper bound(%)', value=50.0, min_value=-90.0, step=1.0,
                                                   key='short_upper')
            short_term_ret_upper /= 100

        st.write('Long Term Return Lookback')
        col111, col222 = st.columns(2)
        with col111:
            # long term ret range
            long_term_ret_lower = st.number_input(label='Lower bound(%)', value=20.0, min_value=-90.0, step=1.0,
                                                  key='long_lower')
            long_term_ret_lower /= 100
        with col222:
            long_term_ret_upper = st.number_input(label='Upper bound(%)', value=100.0, min_value=-90.0, step=1.0,
                                                  key='long_upper')
            long_term_ret_upper /= 100

        # volume lookback
        st.write('Volume Lookback')
        col1111, col2222 = st.columns(2)
        with col1111:
            avg_daily_dollar_vol_lower = st.number_input(label='Average Daily Dollar Volume Lower Bound($)',
                                                         value=100000.0, min_value=0.0, step=0.01)
            median_daily_volume_lower = st.number_input(label='Median Daily Volume Lower Bound($)', value=100000.0,
                                                        min_value=0.0, step=0.01)
        with col2222:
            avg_daily_dollar_vol_upper = st.number_input(label='Average Daily Dollar Volume Upper Bound($)',
                                                         value=1000000.0, min_value=0.0, step=0.01)
            median_daily_volume_upper = st.number_input(label='Median Daily Volume Upper Bound($)', value=1000000.0,
                                                        min_value=0.0, step=0.01)
        # dollar volume ratio range
        st.write('Dollar Volume Ratio Range')
        col11111, col22222 = st.columns(2)
        with col11111:
            dollar_vol_ratio_lower = st.number_input(label='Ratio Lower Bound', min_value=0.0, value=3.0,
                                                     step=0.01)
        with col22222:
            dollar_vol_ratio_upper = st.number_input(label='Ratio Upper Bound', min_value=0.0, value=100.0, step=0.01)

        st.write('Trailing Stop loss')
        col111111, col222222 = st.columns(2)
        with col111111:
            range_test = st.number_input(label='Days Holding Test', min_value=1, value=45, step=1)
            dropdown_allow_in_gain = st.number_input(label='Stop Loss After-Test Period(%)', min_value=0, value=25)

        with col222222:
            stop_loss_test_period = st.number_input(label='Stop Loss Test Period (%)', min_value=1, value=40)
            stop_gain_test_period = st.number_input(label='Stop Gain Resistance Test Period(%)', min_value=1, value=50)


        st.write('Portfolio')
        col111111, col222222 = st.columns(2)
        with col111111:
            cash = st.number_input(label='Initial Investment', min_value=1000, value=10000, step=1)
            slippage = st.number_input(label='Slippage (%)', min_value=0.0, value=2.0, step=0.01)

        with col222222:
            max_weight = st.number_input(label='Max Weight Single Position(%)', min_value=0, value=20)
            min_weight = st.number_input(label='Min Weight Single Position(%)', min_value=0, value=10)




        submitted = st.form_submit_button("Submit")



        if submitted:
            reserch = filter_onePeriod(dataframe=filter_csv, start_date=start_date, end_date=end_date,
                                       price_lower_limit=price_lower_limit, price_upper_limit=price_upper_limit,
                                       short_term_ret_lower=short_term_ret_lower,
                                       short_term_ret_upper=short_term_ret_upper,
                                       long_term_ret_lower=long_term_ret_lower, long_term_ret_upper=long_term_ret_upper,
                                       avg_daily_dollar_vol_lower=avg_daily_dollar_vol_lower,
                                       avg_daily_dollar_vol_upper=avg_daily_dollar_vol_upper,
                                       median_daily_dollar_vol_lower=median_daily_volume_lower,
                                       median_daily_dollar_vol_upper=median_daily_volume_upper,
                                       dollar_vol_ratio_lower=dollar_vol_ratio_lower,
                                       dollar_vol_ratio_upper=dollar_vol_ratio_upper)
            if type(reserch) is tuple or reserch.empty:
                st.write('No Results Avaible')
            else:
                # trailing stop loss
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

                #sell_day = []
                #for count, value in enumerate(stop_loss_ret['actual_holdings']):
                #    af = datetime.datetime.strptime(dates[count], "%Y-%m-%d")
                #    single_sell = af + datetime.timedelta(days=value)
                #    sell_day.append(single_sell.strftime("%Y-%m-%d"))

                # round result
                display_total_df = reserch.copy()
                display_total_df['buy_price'] = pd.Series(
                    ["{0:.2f}".format(val) for val in display_total_df['buy_price']], index=display_total_df.index)
                display_total_df['adjClose_after_holdingPeriod'] = pd.Series(
                    ["{0:.2f}".format(val) for val in display_total_df['adjClose_after_holdingPeriod']],
                    index=display_total_df.index)
                display_total_df['min_price_during_holding_period'] = pd.Series(
                    ["{0:.2f}".format(val) for val in display_total_df['min_price_during_holding_period']],
                    index=display_total_df.index)
                display_total_df['max_price_during_holding_period'] = pd.Series(
                    ["{0:.2f}".format(val) for val in display_total_df['max_price_during_holding_period']],
                    index=display_total_df.index)
                display_total_df['dollar_volume_ratio'] = pd.Series(
                    ["{0:.2f}".format(val) for val in display_total_df['dollar_volume_ratio']],
                    index=display_total_df.index)
                display_total_df['cumulative_return_holdingPeriod'] = pd.Series(
                    ["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in
                     display_total_df['cumulative_return_holdingPeriod']], index=display_total_df.index)
                display_total_df['long_term_look_return'] = pd.Series(
                    ["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in
                     display_total_df['long_term_look_return']], index=display_total_df.index)
                display_total_df['short_term_look_return'] = pd.Series(
                    ["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in
                     display_total_df['short_term_look_return']], index=display_total_df.index)
                display_total_df['avg_daily_volume_over_volume_lookback_period'] = pd.Series(
                    ["{}".format(int(val)) if not math.isnan(val) else "{}".format(val) for val in
                     display_total_df['avg_daily_volume_over_volume_lookback_period']], index=display_total_df.index)
                display_total_df['median_daily_volume_over_volume_lookback_period'] = pd.Series(
                    ["{}".format(int(val)) if not math.isnan(val) else "{}".format(val) for val in
                     display_total_df['median_daily_volume_over_volume_lookback_period']], index=display_total_df.index)

                # run the engine
                reserch['date'] = reserch['date'].astype(str)
                engine = backtester_engine(overall=reserch, dataset=dataset, start_date=start_date, end_date=end_date, cash=cash, transactions_cost=slippage / 100, max_weight=max_weight, min_weight=min_weight)
                engine.run()
                portfolio_rets = pd.Series(engine.cash_series, index=[datetime.datetime.strptime(i, "%Y-%m-%d") for i in engine.timeline]).pct_change(1)
                # generate and save the templates
                sp500 = qs.utils.download_returns('SPY')
                qs.reports.html(portfolio_rets, sp500, output=os.path.join('templates', 'templates.html'), title='Crypto Strategy Tearsheet')

                # output
                st.write('## Output:')
                # performance
                # st.write('Performance:')
                # performance_expander = st.beta_expander(label='Performance')
                # with performance_expander:
                #     trat = get_indicators(reserch)
                #     st.write('Performance:')
                #     trat = trat.set_index('Indicators')
                #     st.table(trat)
                # # month distribution
                # st.write('Month distribution table:')
                # month_expander = st.beta_expander(label='Month distribution')
                # with month_expander:
                #     month_table = month_distribution(reserch)
                #     st.table(month_table)
                # st.write('Median Monthly Return: {}'.format(np.median(month_table['Avg_return'])))
                # st.write('SD Monthly Return: {}'.format(np.std(month_table['Avg_return'])))
                # st.markdown(get_table_download_link(month_table, 'month_distribution'), unsafe_allow_html=True)
                # # month distribution plots
                # st.write('Charts')
                # chart_expander = st.beta_expander(label='Charts')
                # with chart_expander:
                #     generate_charts(month_table)
                # Overall result
                st.write('Overall Results:')
                table_expander = st.beta_expander(label='Overall Table')
                with table_expander:
                    st.table(display_total_df)
                st.write('### Download Overall.csv')
                st.write('Overall.csv')
                st.markdown(get_table_download_link(reserch, 'Overall'), unsafe_allow_html=True)
                st.write('Overall.csv (Rounded)')
                st.markdown(get_table_download_link(display_total_df, 'Overall'), unsafe_allow_html=True)
                # link
                st.write("check out this [link](http://18.118.231.59:8000/)")


def app():
    # initialize
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    submitted = False

    st.title("Back Testing")

    # establish connection pool
    info_placeholder_conn = st.empty()
    with st.spinner("Established tcp connection to database..."):
        tcp = init_tcp()
    info_placeholder_conn.success("Database tcp connection established")
    info_placeholder_conn.empty()
    # fetch overall.csv
    info_placeholder_all = st.empty()
    with st.spinner("Fetching overall.csv..."):
        filter_csv = load_overall()
    info_placeholder_all.success("Overall.csv loaded")
    info_placeholder_all.empty()
    # fetch csv dataset
    datasets = load_dataset(dir_path=os.path.join('data', 'csv'))

    # choose strategy
    strategy_name = st.selectbox(
        label="Strategy", options=["Small Cap Fund Strategy Daily-Restricted", "Portfolio",
                                   "None"]
    )
    # empty strategy
    if strategy_name == "None":
        st.write("No Strategy Selected")

    elif strategy_name == "Small Cap Fund Strategy Daily-Restricted":
        small_cap_fund_daily_restricted(filter_csv, tcp)

    elif strategy_name == "Portfolio":
        portfolio(filter_csv, datasets, tcp)

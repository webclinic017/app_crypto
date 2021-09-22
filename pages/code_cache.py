# from strategy.Small_Cap_Fund_Portfolio import scanning_onePeriod, portfolio
# from strategy.Small_cap_Fund_Daily import one_day_screening, organize_outputs_daily

# def small_cap_fund_strategy_onePeriod(conn, all_symbols):
#     # parameters
#     with st.form("Parameters form:"):
#         # finding parameters
#         st.write("Finding parameters:")
#         col1, col2 = st.beta_columns(2)
#         with col1:
#             price_lower_limit = st.number_input(
#                 label="Price lower bound", min_value=0.0, value=1.0
#             )
#         with col2:
#             price_upper_limit = st.number_input(
#                 label="Price upper bound", value=3.0
#             )
#         observing_date = st.date_input(
#             label="Strategy Start date",
#             value=date(2020, 6, 23),
#             min_value=date(2012, 6, 20),
#             max_value=date(2021, 6, 23),
#         )
#         observing_date = observing_date.strftime("%Y-%m-%d")
#         before_day_limit = st.number_input(
#             label="Look back period", value=45, min_value=1, step=1
#         )
#         cumulative_ret_limit = st.number_input(
#             label="Cumulative Price Limit in look back period(%)",
#             value=100.0,
#             min_value=0.0,
#             step=0.1,
#         )
#         cumulative_ret_limit /= 100
#         averageVol_limit = st.number_input(
#             label="Average daily volume limit", min_value=0, value=3000000, step=1
#         )
#         void_vol_percent_tolerance = st.number_input(
#             label="Void volume tolerance(%)",
#             value=30.0,
#             min_value=0.0,
#             max_value=100.0,
#             step=0.1,
#         )
#         void_vol_percent_tolerance /= 100
#         col11, col22 = st.beta_columns(2)
#         with col11:
#             return_limit_bool = st.checkbox(
#                 label="Limit search on first n", value=True
#             )
#         with col22:
#             return_limit = st.number_input(
#                 label="# of n\n(Effective only when the left item is checked)",
#                 value=10,
#                 min_value=1,
#                 max_value=len(all_symbols),
#                 step=1,
#             )
#         if return_limit_bool:
#             running_symbols = all_symbols[: int(return_limit)]
#         else:
#             running_symbols = all_symbols
#         # strategy parameters
#         st.write("Strategy Parameters")
#         range_test = st.number_input(
#             label="Holding Period", value=45, step=1, min_value=1, max_value=150
#         )  # TODO: change max exception
#         stop_loss_test_period = st.number_input(
#             label="Lost allowed when holding(%)",
#             value=40.0,
#             max_value=100.0,
#             min_value=0.0,
#             step=0.1,
#         )
#         stop_loss_test_period /= -100
#         stop_gain_test_period = st.number_input(
#             label="Gain keep to hold after holding period(%)",
#             value=50.0,
#             max_value=100.0,
#             min_value=0.0,
#             step=0.1,
#         )
#         stop_gain_test_period /= 100
#         dropdown_allow_in_gain = st.number_input(
#             label="Drop down limit to stop loss after holding period(%)",
#             value=25.0,
#             max_value=100.0,
#             min_value=0.0,
#             step=0.1,
#         )
#         dropdown_allow_in_gain /= -100
#         # submit form
#         submitted = st.form_submit_button("Submit", on_click=update_submitted)
#
#     # submitted
#     if submitted or st.session_state.submitted:
#         # finding candidates
#         with st.spinner("Finding candidates fit all conditions..."):
#             candidates = {}
#             for symbol in stqdm(running_symbols):
#                 flag, data = check_single_symbol(
#                     symbol=symbol,
#                     price_lower_limit=price_lower_limit,
#                     price_upper_limit=price_upper_limit,
#                     observing_date=observing_date,
#                     before_day_limit=before_day_limit,
#                     after_day_limit=100,
#                     cumulative_limit=cumulative_ret_limit,
#                     volAverage_limit=averageVol_limit,
#                     void_vol_percent_tolerance=void_vol_percent_tolerance,
#                     conn=conn,
#                     return_data=True,
#                 )
#                 if flag:
#                     candidates[symbol] = data
#         # run strategy in candidates
#         with st.spinner("Running strategy in all candidates..."):
#             strategy_results = {}
#             strategy_actions = {}
#             for symbol in stqdm(candidates.keys()):
#                 cur_result = after_buy(
#                     zio=candidates[symbol],
#                     range_test=range_test,
#                     stop_loss_test_period=stop_loss_test_period,
#                     stop_gain_test_period=stop_gain_test_period,
#                     dropdown_allow_in_gain=dropdown_allow_in_gain,
#                 )
#                 strategy_results[symbol] = cur_result[0]["cumulative_return"]
#                 strategy_actions[symbol] = cur_result[1]
#         all_symbols_expander = st.beta_expander(label="All available symbols:")
#         with all_symbols_expander:
#             st.write(list(candidates.keys()))
#
#         total_expander = st.beta_expander(label="Total Performance")
#         with total_expander:
#             if submitted or st.session_state.submitted:
#                 if not strategy_results:
#                     st.empty()
#
#                 else:
#                     _onePeriod_totalPerformance(strategy_results)
#         single_expander = st.beta_expander(label="Single Stock Performance")
#         with single_expander:
#             if submitted or st.session_state.submitted:
#                 if not strategy_results:
#                     st.empty()
#
#                 else:
#                     selected = st.selectbox(
#                         label="Symbols", options=list(candidates.keys())
#                     )
#                     st.line_chart(data=strategy_results[selected])
#         action_expander = st.beta_expander(label="Strategy Action")
#         with action_expander:
#             if submitted or st.session_state.submitted:
#                 if len(strategy_results) != 0:
#                     selected_actions = st.selectbox(
#                         label="Symbols",
#                         options=list(candidates.keys()),
#                         key="action",
#                     )
#                     for i in strategy_actions[selected_actions]:
#                         st.write(i)
#             else:
#                 st.empty()
#
# def _onePeriod_totalPerformance(strategy_results):
#     st.write("Return Distribution")
#     plot_data = np.array(
#         [
#             strategy_results[symbol][-1]
#             for symbol in strategy_results
#         ]
#     )
#     fig, ax = plt.subplots()
#     ax.hist(plot_data, bins=30, range=(-5, 5))
#     st.pyplot(fig)
#     st.write(f"Average return: {np.mean(plot_data) * 100:.3f}%")
#     st.write(f"Return variance: {np.var(plot_data):.3f}")
#     st.write(f"Skewness of returns: {skew(plot_data):.3f}")
#     st.write(f"Kurtosis of returns: {kurtosis(plot_data):.3f}")
#     st.write(plot_data.tolist())


# def small_cap_fund_onePeriod(conn, all_symbols):
#     with st.form("Form2:"):
#         # scaning parameters
#         st.write('### Scaning Parameters')
#         start_date = st.date_input(
#             label="Start date",
#             value=date(2018, 7, 11),
#             min_value=date(2012, 6, 20),
#             max_value=date(2021, 6, 23),
#         )
#         start_date = start_date.strftime("%Y-%m-%d")  # start date
#         # price range
#         st.write('Price Range')
#         col1, col2 = st.beta_columns(2)
#         with col1:
#             price_lower_limit = st.number_input(
#                 label="Price lower bound($)", min_value=0.0, value=1.0
#             )
#         with col2:
#             price_upper_limit = st.number_input(
#                 label="Price upper bound($)", value=3.0
#             )
#         # Return lookback
#         st.write('Short Term Return Lookback')
#         col11, col22, col33 = st.beta_columns(3)
#         with col11:
#             # short term lookback period
#             short_term_ret_lookback = st.number_input(label='Short Term Lookback Period(trading days)', value=30, min_value=1, step=1)
#         with col22:
#             # short term ret range
#             short_term_ret_lower = st.number_input(label='Lower bound(%)', value=10.0, min_value=0.0, step=1.0, key='short_lower')
#             short_term_ret_lower /= 100
#         with col33:
#             short_term_ret_upper = st.number_input(label='Upper bound(%)', value=50.0, min_value=0.0, step=1.0, key='short_upper')
#             short_term_ret_upper /= 100
#
#         st.write('Long Term Return Lookback')
#         col111, col222, col333 = st.beta_columns(3)
#         with col111:
#             # long term return lookback period
#             long_term_ret_lookback = st.number_input(label='Long Term Lookback Period(trading days)', value=100, min_value=1, step=1)
#         with col222:
#             # long term ret range
#             long_term_ret_lower = st.number_input(label='Lower bound(%)', value=10.0, min_value=0.0, step=1.0, key='long_lower')
#             long_term_ret_lower /= 100
#         with col333:
#             long_term_ret_upper = st.number_input(label='Upper bound(%)', value=100.0, min_value=0.0, step=1.0, key='long_upper')
#             long_term_ret_upper /= 100
#
#         # volume lookback
#         st.write('Volume Lookback')
#         col1111, col2222, col3333 = st.beta_columns(3)
#         with col1111:
#             vol_lookback = st.number_input(label='Volume Lookback Period(trading days)', value=10, min_value=1)
#         with col2222:
#             avg_daily_dollar_vol_lower = st.number_input(label='Average Daily Dollar Volume Lower Bound($)', value=100000.0, min_value=0.0, step=0.01)
#             median_daily_volume_lower = st.number_input(label='Median Daily Volume Lower Bound($)', value=100000.0, min_value=0.0, step=0.01)
#         with col3333:
#             avg_daily_dollar_vol_upper = st.number_input(label='Average Daily Dollar Volume Upper Bound($)', value=1000000.0, min_value=0.0, step=0.01)
#             median_daily_volume_upper = st.number_input(label='Median Daily Volume Upper Bound($)', value=1000000.0, min_value=0.0, step=0.01)
#         # dollar volume ratio range
#         st.write('Dollar Volume Ratio Range')
#         col11111, col22222, col33333, col44444 = st.beta_columns(4)
#         with col11111:
#             dollar_vol_ratio_short = st.number_input(label='Short Range(last n trading days)', min_value=1, value=10, step=1)
#         with col22222:
#             dollar_vol_ratio_long = st.number_input(label='Long Range(last n trading days)', min_value=1, value=60, step=1)
#         with col33333:
#             dollar_vol_ratio_lower = st.number_input(label='Ratio Lower Bound', min_value=0.0, value=3.0, step=0.01)
#         with col44444:
#             dollar_vol_ratio_upper = st.number_input(label='Ratio Upper Bound', min_value=0.0, value=100.0, step=0.01)
#         # TODO: test
#         col1111111, col222222 = st.beta_columns(2)
#         with col1111111:
#             return_limit_bool = st.checkbox(
#                 label="Limit search on first n", value=False
#             )
#         with col222222:
#             return_limit = st.number_input(
#                 label="# of n\n(Effective only when the left item is checked)",
#                 value=100,
#                 min_value=1,
#                 max_value=len(all_symbols),
#                 step=1,
#             )
#         if return_limit_bool:
#             running_symbols = all_symbols[: int(return_limit)]
#         else:
#             running_symbols = all_symbols
#
#         # strategy parameters
#         st.write('### Strategy Parameters')
#         start_value = st.number_input(label='Start Value($)', value=100000, min_value=0, step=1)  # start value
#         holding_period = st.number_input(label='Holding Period(trading days)', value=30, min_value=1, step=1)  # holding period
#         max_weight = st.number_input(label='Maximum weight per holding(%)', value=20.0, min_value=0.0, step=0.1)
#         max_weight = max_weight * 100
#         liquidity = st.number_input(label='Liquidity', value=0.0, min_value=0.0, step=0.1)
#         max_weight = max_weight / 100.0  # Maximum weight per holding
#
#         # submit
#         submitted = st.form_submit_button("Submit", on_click=update_submitted)
#
#         # if submitted
#         if submitted or st.session_state.submitted:
#             # finding candidates
#             with st.spinner("Finding candidates fit all conditions..."):
#                 candidates_df = {}
#                 candidates_measurements = {}
#                 for symbol in stqdm(running_symbols):
#                     flag, df, obs = scanning_onePeriod(symbol=symbol,
#                                                        date=start_date,
#                                                        holding_period=holding_period,
#                                                        price_lower_limit=price_lower_limit,
#                                                        price_upper_limit=price_upper_limit,
#                                                        short_term_ret_lookback=short_term_ret_lookback,
#                                                        short_term_ret_lower=short_term_ret_lower,
#                                                        short_term_ret_upper=short_term_ret_upper,
#                                                        long_term_ret_lookback=long_term_ret_lookback,
#                                                        long_term_ret_lower=long_term_ret_lower,
#                                                        long_term_ret_upper=long_term_ret_upper,
#                                                        vol_lookback=vol_lookback,
#                                                        avg_daily_dollar_vol_lower=avg_daily_dollar_vol_lower,
#                                                        avg_daily_dollar_vol_upper=avg_daily_dollar_vol_upper,
#                                                        median_daily_dollar_vol_lower=median_daily_volume_lower,
#                                                        median_daily_dollar_vol_upper=median_daily_volume_upper,
#                                                        dollar_vol_ratio_short=dollar_vol_ratio_short,
#                                                        dollar_vol_ratio_long=dollar_vol_ratio_long,
#                                                        dollar_vol_ratio_lower=dollar_vol_ratio_lower,
#                                                        dollar_vol_ratio_upper=dollar_vol_ratio_upper,
#                                                        conn=conn)
#                     if flag:
#                         candidates_df[symbol] = df
#                         candidates_measurements[symbol] = obs
#             # strategy part
#             if len(candidates_df) == 0 or len(candidates_measurements) == 0:
#                 st.write("No Results")
#             else:
#                 with st.spinner("Running strategy in all candidates..."):
#                     overall_porfolio, weight_function_output, output_indicators, portfolio_df = portfolio(list_stock_selected=list(candidates_df.keys()), stocks_dictionary=candidates_df,
#                                                                                                           candidates_measurements=candidates_measurements,
#                                                                                                           max_weight=max_weight,
#                                                                                                           liquidity=liquidity,
#                                                                                                           initial_investment=start_value,
#                                                                                                           number_days_before_rebalance=holding_period)
#
#                 # output
#                 st.write('## Portfolio Analysis')
#                 st.write('### Weight Function Detail:')
#                 st.write(weight_function_output[0])
#                 st.write('### Portfolio Table')
#                 overall_porfolio_expander = st.beta_expander(label='Overall Portfolio Table')
#                 with overall_porfolio_expander:
#                     # round output
#                     display_overall_porfolio = overall_porfolio.copy()
#                     display_overall_porfolio = display_overall_porfolio.round({'portfolio_value': 2, 'daily_ret': 4, 'weight': 4, 'adjClose':2, 'cumulative_return':3, 'long_term_look_return':3, 'short_term_look_return':3, 'avg_daily_volume_over_volume_lookback_period':0, 'median_daily_volume_over_volume_lookback_period': 0, 'dollar_volume_ratio': 0})
#                     display_overall_porfolio['portfolio_value'] = pd.Series(["{0:.2f}".format(val) for val in display_overall_porfolio['portfolio_value']], index = display_overall_porfolio.index)
#                     display_overall_porfolio['daily_ret'] = pd.Series(["{0:.2f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in display_overall_porfolio['daily_ret']], index = display_overall_porfolio.index)
#                     display_overall_porfolio['weight'] = pd.Series(["{0:.4f}".format(val) for val in display_overall_porfolio['weight']], index = display_overall_porfolio.index)
#                     display_overall_porfolio['adjClose'] = pd.Series(["{0:.2f}".format(val) for val in display_overall_porfolio['adjClose']], index = display_overall_porfolio.index)
#                     display_overall_porfolio['cumulative_return'] = pd.Series(["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in display_overall_porfolio['cumulative_return']], index = display_overall_porfolio.index)
#                     display_overall_porfolio['long_term_look_return'] = pd.Series(["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in display_overall_porfolio['long_term_look_return']], index = display_overall_porfolio.index)
#                     display_overall_porfolio['short_term_look_return'] = pd.Series(["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in display_overall_porfolio['short_term_look_return']], index = display_overall_porfolio.index)
#                     display_overall_porfolio['avg_daily_volume_over_volume_lookback_period'] = pd.Series(["{}".format(int(val)) if not math.isnan(val) else "{}".format(val) for val in display_overall_porfolio['avg_daily_volume_over_volume_lookback_period']], index = display_overall_porfolio.index)
#                     display_overall_porfolio['median_daily_volume_over_volume_lookback_period'] = pd.Series(["{}".format(int(val)) if not math.isnan(val) else "{}".format(val) for val in display_overall_porfolio['median_daily_volume_over_volume_lookback_period']], index = display_overall_porfolio.index)
#                     display_overall_porfolio['dollar_volume_ratio'] = pd.Series(["{0:.2f}".format(val) for val in display_overall_porfolio['dollar_volume_ratio']], index = display_overall_porfolio.index)
#                     st.table(display_overall_porfolio)
#                 st.write('Overall Portfolio Performance .csv(rounded)')
#                 st.markdown(get_table_download_link(display_overall_porfolio, 'Overall_Portfolio'), unsafe_allow_html=True)
#                 st.write('Overall Portfolio Performance .csv')
#                 st.markdown(get_table_download_link(overall_porfolio, 'Overall_Portfolio'), unsafe_allow_html=True)
#                 st.write('### Yearly Performance')
#                 for i in output_indicators:
#                     st.write(i)
#                 st.line_chart(portfolio_df.cumulative_ret)

# def small_cap_fund_daily(conn, all_symbols):
#     with st.form("Form3:"):
#         # scaning parameters
#         st.write('### Scaning Parameters')
#         # start date and end date
#         st.write('Date Range')
#         col1, col2 = st.beta_columns(2)
#         with col1:
#             start_date = st.date_input(
#                 label="Start date",
#                 value=date(2018, 7, 11),
#                 min_value=date(2007, 1, 2),

#                 max_value=date(2021, 6, 23),
#             )
#         with col2:
#             end_date = st.date_input(
#                 label="End date",
#                 value=date(2018, 8, 10),
#                 min_value=date(2007, 1, 2),
#                 max_value=date(2021, 6, 23)
#             )
#         start_date = start_date.strftime("%Y-%m-%d")  # start date
#         end_date = end_date.strftime("%Y-%m-%d")  # end date
#         # price range
#         st.write('Price Range')
#         col1, col2 = st.beta_columns(2)
#         with col1:
#             price_lower_limit = st.number_input(
#                 label="Price lower bound($)", min_value=0.0, value=3.0  # TODO test
#             )
#         with col2:
#             price_upper_limit = st.number_input(
#                 label="Price upper bound($)", value=6.0  # TODO: test
#             )
#         # Return lookback
#         st.write('Short Term Return Lookback')
#         col11, col22, col33 = st.beta_columns(3)
#         with col11:
#             # short term lookback period
#             short_term_ret_lookback = st.number_input(label='Short Term Lookback Period(trading days)', value=30,
#                                                       min_value=1, step=1)
#         with col22:
#             # short term ret range
#             short_term_ret_lower = st.number_input(label='Lower bound(%)', value=10.0, min_value=0.0, step=1.0,
#                                                    key='short_lower')  # TODO: test
#             short_term_ret_lower /= 100
#         with col33:
#             short_term_ret_upper = st.number_input(label='Upper bound(%)', value=50.0, min_value=0.0, step=1.0,
#                                                    key='short_upper')
#             short_term_ret_upper /= 100

#         st.write('Long Term Return Lookback')
#         col111, col222, col333 = st.beta_columns(3)
#         with col111:
#             # long term return lookback period
#             long_term_ret_lookback = st.number_input(label='Long Term Lookback Period(trading days)', value=100,
#                                                      min_value=1, step=1)
#         with col222:
#             # long term ret range
#             long_term_ret_lower = st.number_input(label='Lower bound(%)', value=20.0, min_value=0.0, step=1.0,
#                                                   key='long_lower')  # TODO: test
#             long_term_ret_lower /= 100
#         with col333:
#             long_term_ret_upper = st.number_input(label='Upper bound(%)', value=100.0, min_value=0.0, step=1.0,
#                                                   key='long_upper')  # TODO: test
#             long_term_ret_upper /= 100

#         # volume lookback
#         st.write('Volume Lookback')
#         col1111, col2222, col3333 = st.beta_columns(3)
#         with col1111:
#             vol_lookback = st.number_input(label='Volume Lookback Period(trading days)', value=10, min_value=1)
#         with col2222:
#             avg_daily_dollar_vol_lower = st.number_input(label='Average Daily Dollar Volume Lower Bound($)',
#                                                          value=100000.0, min_value=0.0, step=0.01)  # TODO: test
#             median_daily_volume_lower = st.number_input(label='Median Daily Volume Lower Bound($)', value=100000.0,
#                                                         min_value=0.0, step=0.01)  # TODO: test
#         with col3333:
#             avg_daily_dollar_vol_upper = st.number_input(label='Average Daily Dollar Volume Upper Bound($)',
#                                                          value=1000000.0, min_value=0.0, step=0.01)
#             median_daily_volume_upper = st.number_input(label='Median Daily Volume Upper Bound($)', value=1000000.0,
#                                                         min_value=0.0, step=0.01)
#         # dollar volume ratio range
#         st.write('Dollar Volume Ratio Range')
#         col11111, col22222, col33333, col44444 = st.beta_columns(4)
#         with col11111:
#             dollar_vol_ratio_short = st.number_input(label='Short Range(last n trading days)', min_value=1, value=10,
#                                                      step=1)
#         with col22222:
#             dollar_vol_ratio_long = st.number_input(label='Long Range(last n trading days)', min_value=1, value=60,
#                                                     step=1)
#         with col33333:
#             dollar_vol_ratio_lower = st.number_input(label='Ratio Lower Bound', min_value=0.0, value=3.0,
#                                                      step=0.01)  # TODO: test
#         with col44444:
#             dollar_vol_ratio_upper = st.number_input(label='Ratio Upper Bound', min_value=0.0, value=100.0, step=0.01)
#         col1111111, col222222 = st.beta_columns(2)
#         with col1111111:
#             return_limit_bool = st.checkbox(
#                 label="Limit search on first n", value=False  # TODO: test
#             )
#         with col222222:
#             return_limit = st.number_input(
#                 label="# of n\n(Effective only when the left item is checked)",
#                 value=50,
#                 min_value=1,
#                 max_value=len(all_symbols),
#                 step=1,
#             )
#         if return_limit_bool:
#             running_symbols = all_symbols[: int(return_limit)]
#         else:
#             running_symbols = all_symbols

#         # strategy parameters
#         st.write('### Strategy Parameters')
#         holding_period = st.number_input(label='Holding Period(trading days)', value=30, min_value=1,
#                                          step=1)  # holding period

#         # submit
#         submitted = st.form_submit_button("Submit", on_click=update_submitted)

#         # submitted
#         if submitted or st.session_state.submitted:
#             # generate date series
#             us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())
#             date_series = list(pd.date_range(start=start_date, end=end_date, freq=us_bd))
#             date_series = [i.strftime("%Y-%m-%d") for i in date_series]

#             # loop for all days
#             with st.spinner("Finding candidates fit all conditions..."):
#                 total_result_symbols = {}
#                 total_result_obs = {}
#                 for cur_date in stqdm(date_series, desc='Runnuing on dates...'):
#                     candidates_df = {}
#                     candidates_measurements = {}
#                     for symbol in stqdm(running_symbols, desc='Running on symbols...'):
#                         flag, df, obs = scanning_onePeriod(symbol=symbol,
#                                                            date=cur_date,
#                                                            holding_period=holding_period,
#                                                            price_lower_limit=price_lower_limit,
#                                                            price_upper_limit=price_upper_limit,
#                                                            short_term_ret_lookback=short_term_ret_lookback,
#                                                            short_term_ret_lower=short_term_ret_lower,
#                                                            short_term_ret_upper=short_term_ret_upper,
#                                                            long_term_ret_lookback=long_term_ret_lookback,
#                                                            long_term_ret_lower=long_term_ret_lower,
#                                                            long_term_ret_upper=long_term_ret_upper,
#                                                            vol_lookback=vol_lookback,
#                                                            avg_daily_dollar_vol_lower=avg_daily_dollar_vol_lower,
#                                                            avg_daily_dollar_vol_upper=avg_daily_dollar_vol_upper,
#                                                            median_daily_dollar_vol_lower=median_daily_volume_lower,
#                                                            median_daily_dollar_vol_upper=median_daily_volume_upper,
#                                                            dollar_vol_ratio_short=dollar_vol_ratio_short,
#                                                            dollar_vol_ratio_long=dollar_vol_ratio_long,
#                                                            dollar_vol_ratio_lower=dollar_vol_ratio_lower,
#                                                            dollar_vol_ratio_upper=dollar_vol_ratio_upper,
#                                                            conn=conn)
#                         if flag:
#                             candidates_df[symbol] = df
#                             candidates_measurements[symbol] = obs
#                     total_result_symbols[cur_date] = candidates_df
#                     total_result_obs[cur_date] = candidates_measurements

#             # strategy
#             with st.spinner("Analyzing Trading Actions..."):
#                 total_outputs = {}
#                 for cur_date in stqdm(date_series, desc='Runnuing on dates...'):
#                     total_outputs[cur_date] = one_day_screening(total_result_symbols[cur_date],
#                                                                 total_result_obs[cur_date], period=holding_period)

#             with st.spinner('Organizing to dataframe:'):
#                 # organize to dataframe
#                 total_df = organize_outputs_daily(total_outputs)
#                 # round result
#                 display_total_df = total_df.copy()
#                 display_total_df['buy_price'] = pd.Series(
#                     ["{0:.2f}".format(val) for val in display_total_df['buy_price']], index=display_total_df.index)
#                 display_total_df['adjClose_after_holdingPeriod'] = pd.Series(
#                     ["{0:.2f}".format(val) for val in display_total_df['adjClose_after_holdingPeriod']],
#                     index=display_total_df.index)
#                 display_total_df['min_price_during_holding_period'] = pd.Series(
#                     ["{0:.2f}".format(val) for val in display_total_df['min_price_during_holding_period']],
#                     index=display_total_df.index)
#                 display_total_df['max_price_during_holding_period'] = pd.Series(
#                     ["{0:.2f}".format(val) for val in display_total_df['max_price_during_holding_period']],
#                     index=display_total_df.index)
#                 display_total_df['dollar_volume_ratio'] = pd.Series(
#                     ["{0:.2f}".format(val) for val in display_total_df['dollar_volume_ratio']],
#                     index=display_total_df.index)
#                 display_total_df['cumulative_return_holdingPeriod'] = pd.Series(
#                     ["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in
#                      display_total_df['cumulative_return_holdingPeriod']], index=display_total_df.index)
#                 display_total_df['long_term_look_return'] = pd.Series(
#                     ["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in
#                      display_total_df['long_term_look_return']], index=display_total_df.index)
#                 display_total_df['short_term_look_return'] = pd.Series(
#                     ["{0:.1f}%".format(val * 100) if not math.isnan(val) else "{}".format(val) for val in
#                      display_total_df['short_term_look_return']], index=display_total_df.index)
#                 display_total_df['avg_daily_volume_over_volume_lookback_period'] = pd.Series(
#                     ["{}".format(int(val)) if not math.isnan(val) else "{}".format(val) for val in
#                      display_total_df['avg_daily_volume_over_volume_lookback_period']], index=display_total_df.index)
#                 display_total_df['median_daily_volume_over_volume_lookback_period'] = pd.Series(
#                     ["{}".format(int(val)) if not math.isnan(val) else "{}".format(val) for val in
#                      display_total_df['median_daily_volume_over_volume_lookback_period']], index=display_total_df.index)

#             # outputs
#             # st.write('Test')
#             # st.write(total_result_symbols)
#             # st.write(total_outputs['2018-07-12'])
#             # st.write(total_result_symbols['2018-07-12']['AAVVF'])
#             st.write('## Output:')
#             st.write('Overall Results:')
#             table_expander = st.beta_expander(label='Overall Table')
#             with table_expander:
#                 st.table(display_total_df)
#             st.write('### Download .csv')
#             st.write('Overall.csv')
#             st.markdown(get_table_download_link(total_df, 'Overall'), unsafe_allow_html=True)
#             st.write('Overall.csv (Rounded)')
#             st.markdown(get_table_download_link(display_total_df, 'Overall'), unsafe_allow_html=True)

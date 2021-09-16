# portfolio.py


# dependencies
import os
import random
import streamlit as st
import datetime as dt
import streamlit as st
from dataclasses import dataclass
from sortedcontainers import SortedList
from stqdm import stqdm


# trading action class
@dataclass(frozen=True)
class TradingActionSingle:
    symbol: str
    date: str
    date2: str = ""
    size: int = 0


class TradingActions:
    def __init__(self):
        self.actions = SortedList([], key=lambda action: action.date)

    def add_buy_record(self, symbols: list, dates: list, dates2: list = None):
        for cur_symbol, cur_buy_date, cur_sell_date in zip(symbols, dates, dates2):
            self.actions.add(TradingActionSingle(cur_symbol, cur_buy_date, cur_sell_date))

    def add_sell_record(self, add_list):
        self.actions.update(add_list)

    # pop by buy date
    def pop_by_date(self, date: str) -> list:
        result = []

        while len(self.actions) != 0 and self.actions[0].date == date:
            result.append(self.actions.pop(0))

        return result


# timeline function
def timeline(start_date, end_date):
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')

    cur_dt = start_date
    date_step = dt.timedelta(days=1)
    date_series = [start_date.strftime('%Y-%m-%d')]

    while cur_dt < end_date:
        cur_dt += date_step
        date_series.append(cur_dt.strftime('%Y-%m-%d'))

    return date_series


# engine
class backtester_engine:
    def __init__(self, overall, dataset, start_date, end_date, cash=1000000.0, transactions_cost=0.0, max_weight=20,
                 min_weight=10):
        # properties
        self.original_cash = cash
        self.dataset = dataset
        self.cur_cash = cash
        self.max_weight = max_weight
        self.min_weight = min_weight
        self.transactions_cost = transactions_cost
        self.cash_series = []
        self.portfolio_stocks_value = 0
        self.portfolio_value_series = []
        self.log_str = []
        # generate the timeline
        self.timeline = timeline(start_date, end_date)
        # generate the trading actions
        trading_symbols = overall['stocks'].tolist()
        trading_buydates = overall['date'].tolist()
        trading_selldates = [(dt.datetime.strptime(date, '%Y-%m-%d') + dt.timedelta(days=days)).strftime('%Y-%m-%d') for
                             date, days in zip(trading_buydates, overall['actual_holding_period'].tolist())]
        self.buyactions = TradingActions()
        self.buyactions.add_buy_record(trading_symbols, trading_buydates, trading_selldates)
        self.sellactions = TradingActions()

    def log(self, dt, txt, warning=False):
        if not warning:
            self.log_str.append(f'INFO: {dt} {txt}')
        else:
            self.log_str.append(f'WARNING: {dt} {txt}')

    def buy(self, cur_date):
        if self.cur_cash <= 0:
            investments = []
        else:
            investments = []
            buy = self.buyactions.pop_by_date(cur_date)
            list_candidates = []
            for symbol in range(len(buy)):
                day_symbols = {'symbol': [], 'buy_day': [], 'price': [], 'sell_date': []}
                day_symbols['symbol'] = buy[symbol].symbol
                day_symbols['buy_day'] = cur_date
                day_symbols['price'] = self.dataset[buy[symbol].symbol].retrieve_by_date(cur_date).adjClose
                day_symbols['sell_date'] = buy[symbol].date2
                list_candidates.append(day_symbols)

            if list_candidates:
                list_stock_selected = []
                for symbol_records in list_candidates:
                    list_stock_selected.append(symbol_records['symbol'])

                portfolio_value = self.portfolio_stocks_value + self.cur_cash  #FIXME:

                # check if there are stock to invest or not
                if list_stock_selected:
                    # print('2')
                    max_perc = self.max_weight / 100
                    min_perc = self.min_weight / 100
                    # check if the vector is empty
                    stock_to_invest = {'stock': [], 'buy_day': [], 'price': [], 'money_to_invest': [], 'size': [],
                                       'sell_date': []}
                    for i in list_stock_selected:
                        if self.cur_cash >= max_perc * portfolio_value:
                            list_stock_selected = random.choices(list_stock_selected, k=len(list_stock_selected))
                            for single_candidate in list_candidates:
                                if i == single_candidate['symbol']:
                                    stock_to_invest['stock'] = single_candidate['symbol']
                                    stock_to_invest['size'] = (max_perc * portfolio_value) / (single_candidate['price']*(1 + self.transactions_cost))
                                    stock_to_invest['money_to_invest'] = max_perc * portfolio_value
                                    stock_to_invest['buy_day'] = single_candidate['buy_day']
                                    stock_to_invest['price'] = single_candidate['price']
                                    stock_to_invest['sell_date'] = single_candidate['sell_date']
                            investments.append(stock_to_invest)
                            self.cur_cash = self.cur_cash - (max_perc * portfolio_value)
                        elif max_perc * portfolio_value > self.cur_cash >= (min_perc * portfolio_value):
                            list_stock_selected = random.choices(list_stock_selected, k=len(list_stock_selected))
                            for single_candidate in list_candidates:
                                if i == single_candidate['symbol']:
                                    stock_to_invest['stock'] = single_candidate['symbol']
                                    stock_to_invest['size'] = self.cur_cash / (single_candidate['price'] * (1 + self.transactions_cost))
                                    stock_to_invest['money_to_invest'] = self.cur_cash
                                    stock_to_invest['buy_day'] = single_candidate['buy_day']
                                    stock_to_invest['price'] = single_candidate['price']
                                    stock_to_invest['sell_date'] = single_candidate['sell_date']
                            investments.append(stock_to_invest)
                            self.cur_cash = 0
                        else:
                            pass
                else:
                    investments
            else:
                investments

        if investments:
            cur_actions = []
            for i in investments:
                if len(i['stock']) != 1:
                    # log
                    self.log(dt=cur_date, txt=f"Buy {i['stock']} at price at {i['price']} with size of {i['size']}")
                    # construct action series
                    cur_actions.append(TradingActionSingle(symbol=i['stock'], date=i['sell_date'], size=i['size']))
            self.sellactions.add_sell_record(cur_actions)
        # update portfolio series
        st.write(self.portfolio_stocks_value) #! test code
        portfolio_value = self.portfolio_stocks_value + self.cur_cash #! stock value is not updating
        self.portfolio_value_series.append(portfolio_value) #! test code

    def sell(self, cur_date):
        sell = self.sellactions.pop_by_date(cur_date)
        for cur_action in sell:
            cur_symbol = cur_action.symbol
            # retrieve size & price
            cur_size = cur_action.size
            # try:
            cur_price = self.dataset[cur_symbol].retrieve_by_date(cur_date).adjClose
            # except:
            #     cur_price = self.dataset[cur_symbol].retrieve_by_date((dt.datetime.strptime(cur_date, '%Y-%m-%d') - dt.timedelta(days=1)).strftime('%Y-%m-%d')).adjClose
            # log & change cash
            self.log(dt=cur_date, txt=f"Sell {cur_symbol} at price at {cur_price} with size of {cur_size}")
            self.cur_cash += cur_size * cur_price * (1 - self.transactions_cost)

    def run(self):
        # clear log file
        if os.path.isfile('Trading_Log.log'):
            with open('Trading_Log.log', 'w'):
                pass
        # run
        for cur_date in stqdm(self.timeline):
            self.sell(cur_date)
            # buy later
            self.buy(cur_date)
            # update portfolio value
            self.cash_series.append(self.cur_cash)

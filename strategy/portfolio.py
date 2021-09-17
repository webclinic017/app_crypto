# portfolio.py


# dependencies
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
    buy_price: float = 0.0


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
    def __init__(self, overall, dataset, start_date, end_date, cash=1000000.0, transactions_cost=0.0, max_weight=20, min_weight=10):
        # properties
        self.original_cash = cash
        self.dataset = dataset
        self.cur_cash = cash
        self.max_weight = max_weight
        self.min_weight = min_weight
        self.transactions_cost = transactions_cost
        self.portfolio_stocks_value = 0
        self.cash_series = []
        self.portfolio_stocks_value_series = []
        self.record_logs = []
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

    def log(self, cur_date, trans_type, symbol, dollar_vol, price, stock_val, pct_change, cash_balance, portfolio_balance, sell_date, holding_days):
        temp = {"cur_date": cur_date, "trans_type": trans_type, "symbol": symbol, "dollar_vol": dollar_vol, "price": price, "stock_val": stock_val, "pct_change": pct_change, "cash_balance": cash_balance, "portfolio_balance": portfolio_balance, "sell_date": sell_date, "holding_days": holding_days}
        self.record_logs.append(temp)

    def buy(self, cur_date):
        begining_cash = self.cur_cash  # only for log
        symbol_holding = []
        # update portfolio value
        holds = self.sellactions.actions
        portfolio_stocks_value = 0
        symbol_holding = []
        for hold in range(len(holds)):
            symbol_holding.append(holds[hold].symbol)
            price = self.dataset[holds[hold].symbol].retrieve_by_date(cur_date).adjClose
            size = holds[hold].size
            value = price * size
            portfolio_stocks_value += value
        self.portfolio_stocks_value = portfolio_stocks_value

        if self.cur_cash <= 0:
            investments = []
        else:
            investments = []
            buy = self.buyactions.pop_by_date(cur_date)
            list_candidates = []
            for symbol in range(len(buy)):
                day_symbols = {'symbol': [], 'buy_day': [], 'price': [], 'sell_date': [], 'volume': []}
                day_symbols['symbol'] = buy[symbol].symbol
                day_symbols['buy_day'] = cur_date
                day_symbols['price'] = self.dataset[buy[symbol].symbol].retrieve_by_date(cur_date).adjClose
                day_symbols['volume'] = self.dataset[buy[symbol].symbol].retrieve_by_date(cur_date).volume
                day_symbols['sell_date'] = buy[symbol].date2
                list_candidates.append(day_symbols)

            if list_candidates:
                list_stock_selected = []
                for symbol_records in list_candidates:
                    list_stock_selected.append(symbol_records['symbol'])

                portfolio_value = self.portfolio_stocks_value + self.cur_cash
                # avoid to buy stocks we are holding / stop buy until sell
                list_stock_selected = [x for x in list_stock_selected if x not in symbol_holding]
                # check if there are stock to invest or not
                if list_stock_selected:
                    # print('2')
                    max_perc = self.max_weight / 100
                    min_perc = self.min_weight / 100
                    # check if the vector is empty
                    stock_to_invest = {'stock': [], 'buy_day': [], 'price': [], 'money_to_invest': [], 'size': [], 'sell_date': [], 'volume': []}
                    list_stock_selected = random.choices(list_stock_selected, k=len(list_stock_selected))
                    for i in list_stock_selected:
                        if self.cur_cash >= max_perc * portfolio_value:
                            for single_candidate in list_candidates:
                                if i == single_candidate['symbol']:
                                    stock_to_invest['stock'] = single_candidate['symbol']
                                    stock_to_invest['size'] = (max_perc * portfolio_value) / (single_candidate['price']*(1 + self.transactions_cost))
                                    stock_to_invest['money_to_invest'] = max_perc * portfolio_value
                                    stock_to_invest['buy_day'] = single_candidate['buy_day']
                                    stock_to_invest['price'] = single_candidate['price']
                                    stock_to_invest['sell_date'] = single_candidate['sell_date']
                                    stock_to_invest['volume'] = single_candidate['volume']
                            investments.append(stock_to_invest)
                            self.cur_cash = self.cur_cash - max_perc * portfolio_value
                        elif max_perc * portfolio_value > self.cur_cash >= (min_perc * portfolio_value):
                            for single_candidate in list_candidates:
                                if i == single_candidate['symbol']:
                                    stock_to_invest['stock'] = single_candidate['symbol']
                                    stock_to_invest['size'] = self.cur_cash / (single_candidate['price'] * (1 + self.transactions_cost))
                                    stock_to_invest['money_to_invest'] = self.cur_cash
                                    stock_to_invest['buy_day'] = single_candidate['buy_day']
                                    stock_to_invest['price'] = single_candidate['price']
                                    stock_to_invest['sell_date'] = single_candidate['sell_date']
                                    stock_to_invest['volume'] = single_candidate['volume']
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
            portfolio_stocks_value = self.portfolio_stocks_value 
            for i in investments:
                if len(i['stock']) != 1:
                    # log
                    cur_date = i['buy_day']
                    symbol = i['stock']
                    volume = i['volume']
                    price = i['price']
                    size = i['size']
                    self.portfolio_stocks_value += size * price
                    # portfolio_stocks_value += size * price
                    begining_cash -= size * price
                    sell_date = i['sell_date']
                    holding_period = (dt.datetime.strptime(sell_date, "%Y-%m-%d") - dt.datetime.strptime(cur_date, "%Y-%m-%d")).days
                    self.log(cur_date=cur_date, trans_type='buy', symbol=symbol, dollar_vol=(price * volume), price=price, stock_val=price * size, 
                     pct_change=0.0, cash_balance=begining_cash, portfolio_balance=self.portfolio_stocks_value + begining_cash, sell_date=sell_date, holding_days=holding_period)
                    # self.log(cur_date=cur_date, trans_type='buy', symbol=symbol, dollar_vol=(price * volume), price=price, stock_val=price * size, 
                    #  pct_change=0.0, cash_balance=begining_cash, portfolio_balance=portfolio_stocks_value + begining_cash, sell_date=sell_date, holding_days=holding_period)
                    # construct action series
                    cur_actions.append(TradingActionSingle(symbol=i['stock'], date=i['sell_date'], size=i['size'], buy_price=i['price'], date2=cur_date))
            self.sellactions.add_sell_record(cur_actions)

    def sell(self, cur_date):
        sell = self.sellactions.pop_by_date(cur_date)
        for cur_action in sell:
            # get
            symbol = cur_action.symbol
            cur_size = cur_action.size
            cur_price = self.dataset[symbol].retrieve_by_date(cur_date).adjClose
            cur_vol = self.dataset[symbol].retrieve_by_date(cur_date).volume
            buy_price = cur_action.buy_price
            cur_size = cur_action.size
            buy_date = cur_action.date2
            holding_period = (dt.datetime.strptime(cur_date, "%Y-%m-%d") - dt.datetime.strptime(buy_date, "%Y-%m-%d")).days
            # sell: update cash, update
            sell_amount = cur_size * cur_price * (1 - self.transactions_cost)
            self.cur_cash += sell_amount
            self.portfolio_stocks_value -= sell_amount
            # log
            self.log(cur_date=cur_date, trans_type='sell', symbol=symbol, dollar_vol=cur_price * cur_vol, price=cur_price, stock_val=cur_price * cur_size, 
                     pct_change=cur_price / buy_price - 1, cash_balance=self.cur_cash, portfolio_balance=self.portfolio_stocks_value, sell_date=cur_date, holding_days=holding_period)
    
    def hold(self, cur_date):
        for cur_action in self.sellactions.actions:
            # get
            symbol = cur_action.symbol
            buy_price = cur_action.buy_price
            sell_date= cur_action.date
            cur_price = self.dataset[symbol].retrieve_by_date(cur_date).adjClose
            cur_vol = self.dataset[symbol].retrieve_by_date(cur_date).volume
            cur_size = cur_action.size
            buy_date = cur_action.date2
            sell_date = cur_action.date
            holding_period = (dt.datetime.strptime(sell_date, "%Y-%m-%d") - dt.datetime.strptime(buy_date, "%Y-%m-%d")).days
            # log
            self.log(cur_date=cur_date, trans_type='hold', symbol=symbol, dollar_vol=cur_price * cur_vol, price=cur_price, stock_val=cur_price * cur_size, 
                     pct_change=cur_price / buy_price - 1, cash_balance=self.cur_cash, portfolio_balance=self.portfolio_stocks_value + self.cur_cash, sell_date=sell_date, holding_days=holding_period)

    def run(self):
        # clear log file
        self.record_logs = []
        # run
        for cur_date in stqdm(self.timeline):
            # sell
            self.sell(cur_date)
            # buy
            self.buy(cur_date)
            # hold
            self.hold(cur_date)
            # update portfolio value + cash
            self.cash_series.append(self.cur_cash)
            self.portfolio_stocks_value_series.append(self.portfolio_stocks_value)
        # TODO: close all positions

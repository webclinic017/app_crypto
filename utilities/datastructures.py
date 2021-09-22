# datastructures.py


# dependencies
from dataclasses import dataclass
from sortedcontainers import SortedList


# OHLCV data class
@dataclass(frozen=True)
class OHLCV_datapoint:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjClose: float


class OHLCV:
    def __init__(self, ohlc_df):
        # data container & look dict
        self._data = SortedList([], key=lambda datapoint: datapoint.date)
        self._lookup_dict = {}
        # initialize with pandas data
        for index, row in ohlc_df.iterrows():
            self._lookup_dict[row['date']] = index
            self._data.add(
                OHLCV_datapoint(row['date'], row['open'], row['high'], row['low'], row['close'], row['volume'],
                                row['adjClose']))

    def retrieve_by_date(self, date):
        return self._data[self._lookup_dict[date]]


# common_data_retrieving.py
# method to retrieve reused data


import os
import glob
import base64
import concurrent.futures
import psycopg2
import pandas as pd
import streamlit as st
from .DB_connection import run_query_pandas
from .datastructures import OHLCV


@st.cache(
    hash_funcs={psycopg2.extensions.connection: id, "_thread.RLock": id},
    show_spinner=False,
)
def get_all_symbols_list(conn):
    tot_symbol = run_query_pandas("SELECT * FROM tot_symbols", conn)
    symbols_tot = tot_symbol["symbol"].to_list()

    return symbols_tot#sorted(symbols)

def get_all_symbols_list(conn, table_name):
    tot_symbol = run_query_pandas(f'''SELECT * FROM "{table_name}"''', conn)

    return sy


@st.cache(show_spinner=False)
def load_overall():
    return pd.read_csv('data/Overall.csv')

@st.cache(show_spinner=False)
def load_dataset(dir_path, workers=6):
    # helper function: load single
    def load_single(csv_path):
        return OHLCV(pd.read_csv(csv_path))
        # return pd.read_csv(csv_path, parse_dates=['date'], date_parser=lambda x: dt.datetime.strptime(x, '%Y-%m-%d'))

    # csv path
    csv_paths = list(glob.glob(os.path.join(dir_path, '*.csv')))
    csv_names = [os.path.basename(cur_path).split('.')[0] for cur_path in csv_paths]

    # load dataset
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        data = list(pool.map(load_single, csv_paths))
    dataset = {}
    for cur_name, cur_data in zip(csv_names, data):
        dataset[cur_name] = cur_data

    return dataset

def get_table_download_link(df, df_name):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    # csv = df.to_csv(index=False)
    # b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    #
    # return f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'

    csv = df.to_csv().encode()
    b64 = base64.b64encode(csv).decode()

    return f'<a href="data:file/csv;base64,{b64}" download="{df_name}.csv" target="_blank">Download csv file</a>'

# common_data_retrieving.py
# method to retrieve reused data


import base64
import psycopg2
import pandas as pd
import streamlit as st
from .DB_connection import run_query_pandas


@st.cache(
    hash_funcs={psycopg2.extensions.connection: id, "_thread.RLock": id},
    show_spinner=False,
)
def get_all_symbols_list(conn):
    tot_symbol = run_query_pandas("SELECT * FROM tot_symbols", conn)
    symbols_tot = tot_symbol["symbol"].to_list()
    #ex_list = run_query_pandas("SELECT * FROM exceptions", conn)
    #symbols_ex = ex_list["symbol_ex"].to_list()
    #symbols = list(set(symbols_tot) - set(symbols_ex))

    return symbols_tot#sorted(symbols)

@st.cache(show_spinner=False)
def load_overall():
    return pd.read_csv('data/Overall.csv')

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

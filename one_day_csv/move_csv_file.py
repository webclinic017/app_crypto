# dependencies
import os
import psycopg2
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from psycopg2.pool import ThreadedConnectionPool

if __name__ == '__main__':
    # parameters
    num_threads = 10

    # create a folder
    if not os.path.isdir('data'):
        os.mkdir('data')

    # get all symbol list
    conn = psycopg2.connect(dbname="kofifajy", host="raja.db.elephantsql.com", port=5432, user="kofifajy",
                            password='C-Gz_APRee6P08B7y4giyCpq7vo4y_zpDP')
    tot_symbol = pd.read_sql_query("SELECT * FROM tot_symbols", conn)
    symbols_tot = tot_symbol["symbol"].to_list()
    ex_list = pd.read_sql_query("SELECT * FROM exceptions", conn)
    symbols_ex = ex_list["symbol_ex"].to_list()
    symbols = list(set(symbols_tot) - set(symbols_ex))
    symbols = sorted(symbols)
    conn.close()

    # connection pool
    DSN = "postgres://kofifajy:Gz_APRee6P08B7y4giyCpq7vo4y_zpDP@raja.db.elephantsql.com/kofifajy"
    tcp = ThreadedConnectionPool(1, num_threads, DSN)

    # function to save to csv
    def save_to_csv(symbol):
        conn = tcp.getconn()
        temp = pd.read_sql_query("""select * from "{symbol}";""".format(symbol=symbol), conn)
        temp.to_csv(os.path.join('data', '{symbol}.csv'.format(symbol=symbol)))
        tcp.putconn(conn)

    # multithread execution
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        list(tqdm(executor.map(save_to_csv, symbols)))

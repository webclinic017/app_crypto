# DB_connection.py
# utilities function to establish connection and run query


import psycopg2
import pandas as pd
import streamlit as st
from psycopg2.pool import ThreadedConnectionPool


# initiate DB connection
@st.cache(
    allow_output_mutation=True, hash_funcs={"_thread.RLock": id}, show_spinner=False
)
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

# initialize connection pool
@st.cache(hash_funcs={psycopg2.pool.ThreadedConnectionPool: id, "_thread.RLock": id}, show_spinner=False)
def init_tcp():
    #DSN = 'jdbc:postgresql://ls-b5e85ef554c9924819da56c7278214bc2ce922cb.cpnoqscz27nt.us-east-1.rds.amazonaws.com:5432/postgres'
    return ThreadedConnectionPool(1, 11, host = 'ls-b5e85ef554c9924819da56c7278214bc2ce922cb.cpnoqscz27nt.us-east-1.rds.amazonaws.com',
                                  port = 5432, user = "dbmasteruser", dbname = "postgres", password = "r1!U!Rj<G9fQF$^-Qfr1jq=r`EYWsP(.")


# run query
@st.cache(
    ttl=600,
    hash_funcs={psycopg2.extensions.connection: id, "_thread.RLock": id},
    show_spinner=False,
)
def run_query(query, conn):
    with conn.cursor() as cur:
        cur.execute(query)

        return cur.fetchall()


# run query and return pd.Dataframe
@st.cache(
    ttl=600,
    hash_funcs={psycopg2.extensions.connection: id, "_thread.RLock": id},
    show_spinner=False,
)
def run_query_pandas(query, conn):
    return pd.read_sql_query(query, conn)

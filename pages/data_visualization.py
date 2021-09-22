# data_visualization.py
# data visualization page


import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from utilities.DB_connection import init_connection, run_query_pandas
from utilities.common_data_retrieving import (
    get_all_symbols_list,
    get_table_download_link,
)


def app():
    # title
    st.title("Data Visualization")

    # establish database connection
    with st.spinner("Established connection to database..."):
        conn = init_connection()
    info_placeholder_conn = st.empty()
    info_placeholder_conn.success("Database connection established")
    info_placeholder_conn.empty()

    # retrieve all stock symbols
    info_placeholder_all = st.empty()
    with st.spinner("Retrieving all symbol list..."):
        all_symbols = get_all_symbols_list(conn)
    info_placeholder_all.success("All symbols are retrieved")
    info_placeholder_all.empty()

    # pick a symbol
    st.write("### Select a symbol")
    selected_symbol = st.selectbox(label="", options=all_symbols)

    # dataframe
    st.write("### Raw data")
    selected_df = run_query_pandas('''SELECT * FROM "%s"''' % selected_symbol, conn)
    selected_df = selected_df.set_index("date")
    #st.dataframe(selected_df.drop(columns=["symbol"]))
    st.markdown(
        get_table_download_link(selected_df, selected_symbol), unsafe_allow_html=True
    )

    # graph 2
    st.title("Price and Volume")
    tata = make_subplots(rows=2, cols=1)
    tata.add_trace(
        go.Scatter(x=selected_df.index, y=selected_df["adjClose"]), row=1, col=1
    )
    tata.update_yaxes(title_text="Price", row=1, col=1)

    tata.add_trace(go.Bar(x=selected_df.index, y=selected_df["volume"]), row=2, col=1)
    tata.update_yaxes(title_text="Volume", row=2, col=1)

    tata.update_layout(height=600, width=800, showlegend=False, title_x=0.5)
    st.plotly_chart(tata)

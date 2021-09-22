# filter_app.py
# the main function of streamlit app


import streamlit as st
from utilities.multipage import MultiPage
from pages import home, data_visualization, backtesting
from utilities.SessionState import get


# page setting
st.set_page_config(page_title="SmallCaps", page_icon=":dart:", layout='wide')


# pages registration and run
def main():
    # Create an instance of the app
    app = MultiPage()

    # Title of the main page
    st.title("Small Caps App")

    # Add all your applications (pages) here
    app.add_page("Home Page", home.app)
    app.add_page("Data Visualization", data_visualization.app)
    app.add_page("Back Testing", backtesting.app)

    # The main app
    app.run()

if __name__ == "__main__":
    session_state = get(password="")
    if session_state.password != st.secrets["login_password"]:
        title_placeholder = st.empty()
        pwd_placeholder = st.empty()
        title_placeholder.title("Small Caps App")
        pwd = pwd_placeholder.text_input("Password:", value="", type="password")
        session_state.password = pwd
        if session_state.password == st.secrets["login_password"]:
            pwd_placeholder.empty()
            title_placeholder.empty()
            st.balloons()
            main()
        elif session_state.password != "":
            st.info("The password you entered is incorrect")
    else:
        main()
    # main()

# multipage.py
# add multipage to streamlit app, credit to:https://towardsdatascience.com/creating-multipage-applications-using-streamlit-efficiently-b58a58134030


import streamlit as st


class MultiPage:
    def __init__(self) -> None:
        self.pages = []

    def add_page(self, title, func) -> None:
        """Class Method to Add pages to the project
        Args:
            title ([str]): The title of page which we are adding to the list of apps

            func: Python function to render this page in Streamlit
        """

        self.pages.append({"title": title, "function": func})

    def run(self):
        # Dropdown to select the page to run
        page = st.sidebar.selectbox(
            "Navigation", self.pages, format_func=lambda page: page["title"]
        )

        # empty session state
        if page["title"] != "Back Testing":
            if "submitted" in st.session_state:
                st.session_state.submitted = False

        # run the app function
        page["function"]()

import streamlit as st
from tabs import transactions, portfolio, performance

st.set_page_config(
    page_title="Stock Market Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Stock Market Analyzer")

tab1, tab2, tab3 = st.tabs(["Transactions", "Portfolio", "Performance"])

with tab1:
    transactions.render()

with tab2:
    portfolio.render()

with tab3:
    performance.render()

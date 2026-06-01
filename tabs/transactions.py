import streamlit as st
import pandas as pd
from datetime import date

from data import store, loader


def render() -> None:
    st.header("Transactions")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Upload CSV")
        st.caption("Required columns: ticker, quantity, date, price, type")
        uploaded = st.file_uploader("Choose a CSV file", type="csv", key="csv_uploader")
        if uploaded is not None:
            df, error = loader.parse_csv(uploaded)
            if error:
                st.error(f"Parse error: {error}")
            else:
                st.dataframe(df.drop(columns=["source"]), use_container_width=True)
                if st.button("Load into ledger", type="primary"):
                    store.add(df)
                    st.success(f"Loaded {len(df)} transactions.")
                    st.rerun()

    with col2:
        st.subheader("Manual Entry")
        with st.form("manual_form", clear_on_submit=True):
            ticker = st.text_input("Ticker symbol", placeholder="AAPL")
            qty = st.number_input("Quantity", min_value=0.001, step=1.0, format="%.3f")
            txn_date = st.date_input("Transaction date", value=date.today())
            price = st.number_input(
                "Price per share ($)", min_value=0.01, step=0.01, format="%.2f"
            )
            txn_type = st.radio("Transaction type", ["BUY", "SELL"], horizontal=True)
            submitted = st.form_submit_button("Add transaction", type="primary")

        if submitted:
            ticker_clean = ticker.strip().upper()
            if not ticker_clean:
                st.error("Ticker symbol is required.")
            else:
                store.add(pd.DataFrame([{
                    "date": txn_date,
                    "ticker": ticker_clean,
                    "quantity": qty,
                    "price": price,
                    "type": txn_type,
                    "source": "manual",
                }]))
                st.success(
                    f"Added: {txn_type} {qty:.3f} {ticker_clean} @ ${price:.2f}"
                )

    st.divider()
    st.subheader("Transaction Ledger")

    df = store.get()
    if df.empty:
        st.info("No transactions yet. Upload a CSV or enter one manually above.")
        return

    _, btn_col = st.columns([10, 2])
    with btn_col:
        if st.button("Clear all", type="secondary"):
            store.clear()
            st.rerun()

    display = df.copy()
    display["price"] = display["price"].map("${:.2f}".format)
    display["quantity"] = display["quantity"].map("{:.3f}".format)
    st.dataframe(display, use_container_width=True, hide_index=True)
    src_counts = df["source"].value_counts().to_dict()
    st.caption(f"{len(df)} total transactions — {src_counts}")

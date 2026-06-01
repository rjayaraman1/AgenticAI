import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

from data import store
from finance import market, calculations


def render() -> None:
    st.header("Portfolio")

    df = store.get()
    if df.empty:
        st.info("No transactions loaded. Go to the Transactions tab to add data.")
        return

    open_tickers = tuple(df[df["type"] == "BUY"]["ticker"].unique())

    with st.spinner("Fetching current prices..."):
        prices = market.get_prices_bulk(open_tickers)

    portfolio = calculations.compute_portfolio(df, prices)

    if portfolio.empty:
        st.warning("No open positions found.")
        return

    # Summary metric row
    total_value = portfolio["Current Value ($)"].dropna().sum()
    total_cost = portfolio["Cost Basis ($)"].sum()
    total_pnl = total_value - total_cost
    pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Portfolio Value", f"${total_value:,.2f}")
    m2.metric("Total Cost Basis", f"${total_cost:,.2f}")
    m3.metric(
        "Total P&L",
        f"${total_pnl:,.2f}",
        delta=f"{pnl_pct:+.1f}%",
        delta_color="normal",
    )
    m4.metric("Open Positions", str(len(portfolio)))

    st.divider()

    chart_col, _ = st.columns([1, 1])
    with chart_col:
        st.subheader("Portfolio Allocation")
        pie_data = portfolio.dropna(subset=["Current Value ($)"])
        fig = px.pie(
            pie_data,
            values="Current Value ($)",
            names="Ticker",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(margin=dict(t=10, b=10), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    # Risk metrics — fetch 1 year of history for held tickers + SPY
    with st.spinner("Fetching risk data..."):
        risk_start = date.today() - timedelta(days=365)
        risk_prices_raw = market.get_all_historical_prices(
            tuple(portfolio["Ticker"].tolist()) + ("SPY",),
            risk_start,
            date.today(),
        )
        spy_series = (
            risk_prices_raw["SPY"]
            if "SPY" in risk_prices_raw.columns
            else pd.Series(dtype=float)
        )
        ticker_prices = risk_prices_raw.drop(columns=["SPY"], errors="ignore")
        risk_df = calculations.compute_risk_metrics(ticker_prices, spy_series)

    if not risk_df.empty:
        portfolio = portfolio.merge(risk_df, on="Ticker", how="left")

    st.subheader("Stock-wise Breakdown")

    display = portfolio.copy()
    fmt_usd = lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A"
    fmt_pct = lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A"
    fmt_2dp = lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"

    for col in ["Avg Cost ($)", "Current Price ($)", "Cost Basis ($)", "Current Value ($)", "P&L ($)"]:
        display[col] = display[col].apply(fmt_usd)
    display["P&L (%)"] = display["P&L (%)"].apply(fmt_pct)
    display["Quantity"] = display["Quantity"].map("{:.3f}".format)
    if "Volatility (Ann. %)" in display.columns:
        display["Volatility (Ann. %)"] = display["Volatility (Ann. %)"].apply(fmt_2dp)
    if "Beta" in display.columns:
        display["Beta"] = display["Beta"].apply(fmt_2dp)

    st.dataframe(display, use_container_width=True, hide_index=True)

    # Export button — raw numbers, not the formatted display version
    export_df = portfolio.copy()
    st.download_button(
        label="Export portfolio to CSV",
        data=export_df.to_csv(index=False),
        file_name="portfolio_export.csv",
        mime="text/csv",
    )

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date

from data import store
from finance import market, calculations


def render() -> None:
    st.header("Historical Performance")

    df = store.get()
    if df.empty:
        st.info("No transactions loaded. Go to the Transactions tab to add data.")
        return

    open_tickers = tuple(df[df["type"] == "BUY"]["ticker"].unique())

    with st.spinner("Fetching market data..."):
        prices = market.get_prices_bulk(open_tickers)

    portfolio = calculations.compute_portfolio(df, prices)
    metrics = calculations.compute_metrics(df, portfolio)

    if not metrics:
        st.warning("Could not compute metrics.")
        return

    # Metric cards — row 1
    st.subheader("Portfolio Metrics")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Lifetime Investment", f"${metrics['total_invested']:,.2f}")
    c2.metric("Total Proceeds from Sales", f"${metrics['total_proceeds']:,.2f}")
    c3.metric("Current Portfolio Value", f"${metrics['current_value']:,.2f}")

    # Metric cards — row 2
    c4, c5, c6 = st.columns(3)
    sign = "+" if metrics["total_return"] >= 0 else ""
    c4.metric(
        "Total Returns",
        f"${metrics['total_return']:,.2f}",
        delta=f"{sign}{metrics['return_pct']:.1f}%",
    )

    xirr_val = metrics.get("xirr")
    c5.metric(
        "XIRR (Annualized)",
        f"{xirr_val * 100:.2f}%" if xirr_val is not None else "N/A",
    )

    realized_plus_unrealized = metrics["total_proceeds"] + metrics["current_value"]
    c6.metric("Realized + Unrealized Value", f"${realized_plus_unrealized:,.2f}")

    # Trend line
    st.divider()
    st.subheader("Portfolio Value Over Time")

    df["date"] = pd.to_datetime(df["date"])
    all_tickers = tuple(df["ticker"].unique())
    start_date = df["date"].min().date()

    with st.spinner("Reconstructing historical portfolio value..."):
        # Include SPY in the fetch — compute_historical_portfolio_value ignores it
        # (no user transactions for SPY), so portfolio math is unaffected.
        all_prices = market.get_all_historical_prices(
            all_tickers + ("SPY",), start_date, date.today()
        )
        spy_prices = all_prices["SPY"] if "SPY" in all_prices.columns else None
        history = calculations.compute_historical_portfolio_value(df, all_prices)

    if history.empty:
        st.warning("Could not fetch historical price data to build trend line.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=history["date"],
        y=history["value"],
        mode="lines",
        fill="tozeroy",
        line=dict(color="#1f77b4", width=2),
        name="Portfolio Value",
        hovertemplate="<b>%{x}</b><br>Value: $%{y:,.2f}<extra></extra>",
    ))

    # Overlay buy / sell markers on the trend line
    history_dates = set(history["date"])
    for txn_type, color, symbol in [
        ("BUY", "#2ca02c", "triangle-up"),
        ("SELL", "#d62728", "triangle-down"),
    ]:
        txn_dates = set(df[df["type"] == txn_type]["date"].dt.date)
        matching = history[history["date"].isin(history_dates & txn_dates)]
        if not matching.empty:
            fig.add_trace(go.Scatter(
                x=matching["date"],
                y=matching["value"],
                mode="markers",
                marker=dict(color=color, size=12, symbol=symbol),
                name=txn_type,
                hovertemplate=(
                    f"<b>%{{x}}</b><br>{txn_type}<br>"
                    "Portfolio: $%{y:,.2f}<extra></extra>"
                ),
            ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified",
        margin=dict(t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Benchmark comparison — both series indexed to 100 at portfolio start
    if spy_prices is not None and not history.empty:
        st.subheader("Performance vs S&P 500 (Indexed to 100)")

        port_start_date = pd.Timestamp(history["date"].iloc[0])
        port_start_val = history["value"].iloc[0]

        spy_aligned = spy_prices[spy_prices.index >= port_start_date]

        if not spy_aligned.empty:
            spy_start_val = spy_aligned.iloc[0]

            port_indexed = history.copy()
            port_indexed["indexed"] = port_indexed["value"] / port_start_val * 100

            spy_indexed_vals = spy_aligned / spy_start_val * 100
            spy_dates = spy_aligned.index.date

            bench_fig = go.Figure()
            bench_fig.add_trace(go.Scatter(
                x=port_indexed["date"],
                y=port_indexed["indexed"],
                mode="lines",
                line=dict(color="#1f77b4", width=2),
                name="Your Portfolio",
                hovertemplate="<b>%{x}</b><br>Portfolio: %{y:.1f}<extra></extra>",
            ))
            bench_fig.add_trace(go.Scatter(
                x=spy_dates,
                y=spy_indexed_vals.values,
                mode="lines",
                line=dict(color="#ff7f0e", width=2, dash="dash"),
                name="S&P 500 (SPY)",
                hovertemplate="<b>%{x}</b><br>S&P 500: %{y:.1f}<extra></extra>",
            ))
            bench_fig.add_hline(
                y=100,
                line_dash="dot",
                line_color="gray",
                annotation_text="Start (100)",
                annotation_position="right",
            )
            bench_fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Indexed Value (Start = 100)",
                hovermode="x unified",
                margin=dict(t=20, b=10),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
            st.plotly_chart(bench_fig, use_container_width=True)
            st.caption(
                "Both series normalized to 100 at your first portfolio date. "
                "Above 100 = gain; below 100 = loss."
            )

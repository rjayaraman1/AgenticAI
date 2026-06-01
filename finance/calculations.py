import pandas as pd
import numpy as np
from datetime import date
from pyxirr import xirr as _xirr


def compute_portfolio(
    transactions: pd.DataFrame, current_prices: dict[str, float]
) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame()

    rows = []
    for ticker, grp in transactions.groupby("ticker"):
        buys = grp[grp["type"] == "BUY"]
        sells = grp[grp["type"] == "SELL"]

        bought_qty = buys["quantity"].sum()
        sold_qty = sells["quantity"].sum()
        current_qty = bought_qty - sold_qty

        if current_qty <= 0:
            continue

        total_cost = (buys["quantity"] * buys["price"]).sum()
        avg_cost = total_cost / bought_qty if bought_qty > 0 else 0.0

        current_price = current_prices.get(ticker)
        cost_basis = current_qty * avg_cost
        current_value = current_qty * current_price if current_price is not None else None
        pnl = (current_value - cost_basis) if current_value is not None else None
        pnl_pct = (pnl / cost_basis * 100) if (pnl is not None and cost_basis > 0) else None

        rows.append({
            "Ticker": ticker,
            "Quantity": current_qty,
            "Avg Cost ($)": avg_cost,
            "Current Price ($)": current_price,
            "Cost Basis ($)": cost_basis,
            "Current Value ($)": current_value,
            "P&L ($)": pnl,
            "P&L (%)": pnl_pct,
        })

    return pd.DataFrame(rows)


def compute_xirr(transactions: pd.DataFrame, current_value: float) -> float | None:
    if transactions.empty or current_value <= 0:
        return None

    try:
        cash_flows: list[tuple[date, float]] = []
        for _, row in transactions.iterrows():
            amount = float(row["quantity"]) * float(row["price"])
            cf = -amount if row["type"] == "BUY" else amount
            d = pd.Timestamp(row["date"]).date()
            cash_flows.append((d, cf))

        cash_flows.append((date.today(), current_value))

        # XIRR needs at least one positive and one negative cash flow
        amounts = [cf[1] for cf in cash_flows]
        if not (any(a > 0 for a in amounts) and any(a < 0 for a in amounts)):
            return None

        dates, values = zip(*cash_flows)
        result = _xirr(list(dates), list(values))
        return float(result) if result is not None else None
    except Exception:
        return None


def compute_metrics(
    transactions: pd.DataFrame, portfolio_df: pd.DataFrame
) -> dict:
    if transactions.empty:
        return {}

    buys = transactions[transactions["type"] == "BUY"]
    sells = transactions[transactions["type"] == "SELL"]

    total_invested = (buys["quantity"] * buys["price"]).sum()
    total_proceeds = (sells["quantity"] * sells["price"]).sum()

    current_value = 0.0
    if not portfolio_df.empty and "Current Value ($)" in portfolio_df.columns:
        current_value = portfolio_df["Current Value ($)"].dropna().sum()

    total_return = (current_value + total_proceeds) - total_invested
    return_pct = (total_return / total_invested * 100) if total_invested > 0 else 0.0

    return {
        "total_invested": float(total_invested),
        "total_proceeds": float(total_proceeds),
        "current_value": float(current_value),
        "total_return": float(total_return),
        "return_pct": float(return_pct),
        "xirr": compute_xirr(transactions, current_value),
    }


def compute_historical_portfolio_value(
    transactions: pd.DataFrame,
    all_prices: pd.DataFrame,
) -> pd.DataFrame:
    if transactions.empty or all_prices.empty:
        return pd.DataFrame()

    txns = transactions.copy()
    txns["date"] = pd.to_datetime(txns["date"])
    txns["signed_qty"] = txns.apply(
        lambda r: r["quantity"] if r["type"] == "BUY" else -r["quantity"], axis=1
    )

    portfolio_value = pd.Series(0.0, index=all_prices.index)

    for ticker in all_prices.columns:
        ticker_txns = txns[txns["ticker"] == ticker].sort_values("date")
        if ticker_txns.empty:
            continue

        qty_series = ticker_txns.groupby("date")["signed_qty"].sum()
        full_range = pd.date_range(
            all_prices.index.min(), all_prices.index.max(), freq="D"
        )
        qty_daily = (
            qty_series.reindex(full_range, fill_value=0).cumsum().clip(lower=0)
        )
        holdings = qty_daily.reindex(all_prices.index, method="ffill").fillna(0)
        portfolio_value += holdings * all_prices[ticker].ffill()

    result = portfolio_value[portfolio_value > 0].reset_index()
    result.columns = ["date", "value"]
    result["date"] = result["date"].dt.date
    return result


def compute_risk_metrics(
    prices: pd.DataFrame,
    spy_prices: pd.Series,
) -> pd.DataFrame:
    """Annualized volatility and beta vs SPY for each ticker in prices."""
    if prices.empty or spy_prices.empty:
        return pd.DataFrame()

    spy_returns = spy_prices.pct_change().dropna()
    rows = []

    for ticker in prices.columns:
        stock_returns = prices[ticker].pct_change().dropna()
        combined = pd.concat([stock_returns, spy_returns], axis=1, join="inner")
        combined.columns = ["stock", "spy"]
        if len(combined) < 10:
            continue

        volatility = combined["stock"].std() * np.sqrt(252) * 100
        spy_var = combined["spy"].var()
        beta = (
            combined.cov().loc["stock", "spy"] / spy_var
            if spy_var > 0 else None
        )
        rows.append({
            "Ticker": ticker,
            "Volatility (Ann. %)": round(volatility, 2),
            "Beta": round(beta, 2) if beta is not None else None,
        })

    return pd.DataFrame(rows)

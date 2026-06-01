"""
Tests for finance/calculations.py — portfolio math, XIRR, metrics, risk.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
import numpy as np
from datetime import date
from finance.calculations import (
    compute_portfolio,
    compute_xirr,
    compute_metrics,
    compute_risk_metrics,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def txns(*rows):
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# compute_portfolio
# ---------------------------------------------------------------------------

class TestComputePortfolio:

    def test_simple_buy_creates_open_position(self):
        df = txns({"ticker": "AAPL", "quantity": 10, "price": 150.0, "type": "BUY"})
        result = compute_portfolio(df, {"AAPL": 200.0})
        assert len(result) == 1
        row = result.iloc[0]
        assert row["Ticker"] == "AAPL"
        assert row["Quantity"] == 10
        assert row["Current Value ($)"] == pytest.approx(2000.0)

    def test_pnl_calculated_correctly(self):
        df = txns({"ticker": "AAPL", "quantity": 10, "price": 150.0, "type": "BUY"})
        result = compute_portfolio(df, {"AAPL": 200.0})
        assert result.iloc[0]["P&L ($)"] == pytest.approx(500.0)
        assert result.iloc[0]["P&L (%)"] == pytest.approx(33.33, rel=1e-2)

    def test_partial_sell_reduces_quantity(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 150.0, "type": "BUY"},
            {"ticker": "AAPL", "quantity": 4,  "price": 180.0, "type": "SELL"},
        )
        result = compute_portfolio(df, {"AAPL": 200.0})
        assert result.iloc[0]["Quantity"] == 6

    def test_full_sell_excludes_position(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 150.0, "type": "BUY"},
            {"ticker": "AAPL", "quantity": 10, "price": 200.0, "type": "SELL"},
        )
        result = compute_portfolio(df, {"AAPL": 210.0})
        assert result.empty

    def test_avg_cost_weighted_across_multiple_buys(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 100.0, "type": "BUY"},
            {"ticker": "AAPL", "quantity": 10, "price": 200.0, "type": "BUY"},
        )
        result = compute_portfolio(df, {"AAPL": 150.0})
        assert result.iloc[0]["Avg Cost ($)"] == pytest.approx(150.0)

    def test_missing_price_leaves_current_value_null(self):
        df = txns({"ticker": "AAPL", "quantity": 10, "price": 150.0, "type": "BUY"})
        result = compute_portfolio(df, {})
        assert pd.isna(result.iloc[0]["Current Value ($)"])
        assert pd.isna(result.iloc[0]["P&L ($)"])

    def test_multiple_tickers_each_get_own_row(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 150.0, "type": "BUY"},
            {"ticker": "MSFT", "quantity": 5,  "price": 400.0, "type": "BUY"},
            {"ticker": "ORCL", "quantity": 8,  "price": 125.0, "type": "BUY"},
        )
        result = compute_portfolio(df, {"AAPL": 200.0, "MSFT": 450.0, "ORCL": 165.0})
        assert len(result) == 3
        assert set(result["Ticker"]) == {"AAPL", "MSFT", "ORCL"}

    def test_empty_transactions_returns_empty_dataframe(self):
        result = compute_portfolio(pd.DataFrame(), {"AAPL": 200.0})
        assert result.empty


# ---------------------------------------------------------------------------
# compute_xirr
# ---------------------------------------------------------------------------

class TestComputeXirr:

    def test_positive_return_gives_positive_xirr(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 100.0,
             "type": "BUY", "date": date(2023, 1, 1)}
        )
        result = compute_xirr(df, 1200.0)
        assert result is not None
        assert result > 0

    def test_loss_gives_negative_xirr(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 200.0,
             "type": "BUY", "date": date(2023, 1, 1)}
        )
        result = compute_xirr(df, 500.0)
        assert result is not None
        assert result < 0

    def test_empty_transactions_returns_none(self):
        assert compute_xirr(pd.DataFrame(), 1000.0) is None

    def test_zero_current_value_returns_none(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 100.0,
             "type": "BUY", "date": date(2023, 1, 1)}
        )
        assert compute_xirr(df, 0.0) is None

    def test_buy_and_sell_with_profit(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 100.0,
             "type": "BUY",  "date": date(2023, 1, 1)},
            {"ticker": "AAPL", "quantity": 5,  "price": 160.0,
             "type": "SELL", "date": date(2023, 6, 1)},
        )
        result = compute_xirr(df, 800.0)
        assert result is not None
        assert result > 0


# ---------------------------------------------------------------------------
# compute_metrics
# ---------------------------------------------------------------------------

class TestComputeMetrics:

    def test_total_invested_sums_buy_cost(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 100.0, "type": "BUY"},
            {"ticker": "MSFT", "quantity": 5,  "price": 200.0, "type": "BUY"},
        )
        portfolio = pd.DataFrame([{"Current Value ($)": 2500.0}])
        m = compute_metrics(df, portfolio)
        assert m["total_invested"] == pytest.approx(2000.0)

    def test_total_proceeds_sums_sell_revenue(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 100.0, "type": "BUY"},
            {"ticker": "AAPL", "quantity": 3,  "price": 150.0, "type": "SELL"},
        )
        portfolio = pd.DataFrame([{"Current Value ($)": 1400.0}])
        m = compute_metrics(df, portfolio)
        assert m["total_proceeds"] == pytest.approx(450.0)

    def test_total_return_accounts_for_proceeds_and_current_value(self):
        df = txns(
            {"ticker": "AAPL", "quantity": 10, "price": 100.0, "type": "BUY"},
            {"ticker": "AAPL", "quantity": 3,  "price": 150.0, "type": "SELL"},
        )
        portfolio = pd.DataFrame([{"Current Value ($)": 1400.0}])
        m = compute_metrics(df, portfolio)
        # invested=1000, proceeds=450, current=1400 → return = 450+1400-1000 = 850
        assert m["total_return"] == pytest.approx(850.0)

    def test_return_pct_computed_correctly(self):
        df = txns({"ticker": "AAPL", "quantity": 10, "price": 100.0, "type": "BUY"})
        portfolio = pd.DataFrame([{"Current Value ($)": 1500.0}])
        m = compute_metrics(df, portfolio)
        assert m["return_pct"] == pytest.approx(50.0)

    def test_empty_portfolio_value_treated_as_zero(self):
        df = txns({"ticker": "AAPL", "quantity": 10, "price": 100.0, "type": "BUY"})
        m = compute_metrics(df, pd.DataFrame())
        assert m["current_value"] == 0.0

    def test_empty_transactions_returns_empty_dict(self):
        result = compute_metrics(pd.DataFrame(), pd.DataFrame())
        assert result == {}


# ---------------------------------------------------------------------------
# compute_risk_metrics
# ---------------------------------------------------------------------------

class TestComputeRiskMetrics:

    def _make_prices(self, n=252, seed=42):
        rng = np.random.default_rng(seed)
        dates = pd.date_range("2024-01-01", periods=n, freq="B")
        aapl = pd.Series(100 * (1 + rng.normal(0.001, 0.02, n)).cumprod(), index=dates, name="AAPL")
        msft = pd.Series(200 * (1 + rng.normal(0.001, 0.015, n)).cumprod(), index=dates, name="MSFT")
        spy  = pd.Series(400 * (1 + rng.normal(0.0005, 0.01, n)).cumprod(), index=dates, name="SPY")
        prices = pd.DataFrame({"AAPL": aapl, "MSFT": msft})
        return prices, spy

    def test_returns_one_row_per_ticker(self):
        prices, spy = self._make_prices()
        result = compute_risk_metrics(prices, spy)
        assert len(result) == 2
        assert set(result["Ticker"]) == {"AAPL", "MSFT"}

    def test_volatility_is_positive(self):
        prices, spy = self._make_prices()
        result = compute_risk_metrics(prices, spy)
        assert (result["Volatility (Ann. %)"] > 0).all()

    def test_beta_is_numeric(self):
        prices, spy = self._make_prices()
        result = compute_risk_metrics(prices, spy)
        assert result["Beta"].notna().all()

    def test_empty_prices_returns_empty(self):
        result = compute_risk_metrics(pd.DataFrame(), pd.Series(dtype=float))
        assert result.empty

    def test_empty_spy_returns_empty(self):
        prices, _ = self._make_prices()
        result = compute_risk_metrics(prices, pd.Series(dtype=float))
        assert result.empty

    def test_high_vol_stock_has_higher_volatility(self):
        rng = np.random.default_rng(0)
        dates = pd.date_range("2024-01-01", periods=252, freq="B")
        low_vol  = pd.Series((1 + rng.normal(0, 0.005, 252)).cumprod(), index=dates)
        high_vol = pd.Series((1 + rng.normal(0, 0.03,  252)).cumprod(), index=dates)
        spy      = pd.Series((1 + rng.normal(0, 0.01,  252)).cumprod(), index=dates)
        prices   = pd.DataFrame({"LOW": low_vol, "HIGH": high_vol})
        result   = compute_risk_metrics(prices, spy).set_index("Ticker")
        assert result.loc["HIGH", "Volatility (Ann. %)"] > result.loc["LOW", "Volatility (Ann. %)"]

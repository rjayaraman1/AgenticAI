import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import date


@st.cache_data(ttl=300)
def get_current_price(ticker: str) -> float | None:
    try:
        t = yf.Ticker(ticker)
        price = t.fast_info.last_price
        if price and price > 0:
            return float(price)
        hist = t.history(period="5d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return None
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_prices_bulk(tickers: tuple[str, ...]) -> dict[str, float]:
    return {t: p for t in tickers if (p := get_current_price(t)) is not None}


@st.cache_data(ttl=3600)
def get_historical_prices(ticker: str, start: str, end: str) -> pd.Series:
    try:
        hist = yf.Ticker(ticker).history(start=start, end=end)
        if hist.empty:
            return pd.Series(dtype=float, name=ticker)
        if hist.index.tz is not None:
            hist.index = hist.index.tz_convert(None)
        hist.index = hist.index.normalize()
        return hist["Close"].rename(ticker)
    except Exception:
        return pd.Series(dtype=float, name=ticker)


def get_all_historical_prices(
    tickers: tuple[str, ...], start: date, end: date
) -> pd.DataFrame:
    frames: dict[str, pd.Series] = {}
    for ticker in tickers:
        series = get_historical_prices(ticker, str(start), str(end))
        if not series.empty:
            frames[ticker] = series
    if not frames:
        return pd.DataFrame()
    return pd.DataFrame(frames).ffill()

import streamlit as st
import pandas as pd

_KEY = "transactions"
_COLS = ["date", "ticker", "quantity", "price", "type", "source"]


def init() -> None:
    if _KEY not in st.session_state:
        st.session_state[_KEY] = pd.DataFrame(columns=_COLS)


def get() -> pd.DataFrame:
    init()
    return st.session_state[_KEY].copy()


def add(rows: pd.DataFrame) -> None:
    init()
    st.session_state[_KEY] = pd.concat(
        [st.session_state[_KEY], rows], ignore_index=True
    )


def clear() -> None:
    st.session_state[_KEY] = pd.DataFrame(columns=_COLS)

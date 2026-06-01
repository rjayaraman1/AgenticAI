"""
Tests for data/loader.py — CSV parsing and validation.
"""
import io
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
from data.loader import parse_csv


def make_csv(content: str):
    return io.StringIO(content)


VALID_CSV = "ticker,quantity,date,price,type\nAAPL,10,2024-01-15,185.50,BUY\n"


class TestValidInput:
    def test_valid_csv_returns_no_error(self):
        df, err = parse_csv(make_csv(VALID_CSV))
        assert err is None

    def test_valid_csv_row_count(self):
        df, err = parse_csv(make_csv(VALID_CSV))
        assert len(df) == 1

    def test_source_column_set_to_csv(self):
        df, err = parse_csv(make_csv(VALID_CSV))
        assert df.iloc[0]["source"] == "csv"

    def test_ticker_is_uppercased(self):
        csv = make_csv("ticker,quantity,date,price,type\naapl,10,2024-01-15,185.50,buy\n")
        df, err = parse_csv(csv)
        assert err is None
        assert df.iloc[0]["ticker"] == "AAPL"

    def test_type_is_uppercased(self):
        csv = make_csv("ticker,quantity,date,price,type\nMSFT,5,2024-02-01,420.00,buy\n")
        df, err = parse_csv(csv)
        assert err is None
        assert df.iloc[0]["type"] == "BUY"

    def test_column_headers_case_insensitive(self):
        csv = make_csv("TICKER,QUANTITY,DATE,PRICE,TYPE\nAAPL,10,2024-01-15,185.50,BUY\n")
        df, err = parse_csv(csv)
        assert err is None

    def test_sell_transaction_accepted(self):
        csv = make_csv("ticker,quantity,date,price,type\nAAPL,5,2024-06-01,200.00,SELL\n")
        df, err = parse_csv(csv)
        assert err is None
        assert df.iloc[0]["type"] == "SELL"

    def test_multiple_rows_parsed(self):
        csv = make_csv(
            "ticker,quantity,date,price,type\n"
            "AAPL,10,2024-01-15,185.50,BUY\n"
            "MSFT,5,2024-02-01,420.00,BUY\n"
            "ORCL,8,2024-02-15,125.00,BUY\n"
        )
        df, err = parse_csv(csv)
        assert err is None
        assert len(df) == 3


class TestMissingColumns:
    def test_missing_type_column(self):
        csv = make_csv("ticker,quantity,date,price\nAAPL,10,2024-01-15,185.50\n")
        df, err = parse_csv(csv)
        assert err is not None
        assert "type" in err

    def test_missing_ticker_column(self):
        csv = make_csv("quantity,date,price,type\n10,2024-01-15,185.50,BUY\n")
        df, err = parse_csv(csv)
        assert err is not None
        assert "ticker" in err

    def test_missing_multiple_columns(self):
        csv = make_csv("ticker,date\nAAPL,2024-01-15\n")
        df, err = parse_csv(csv)
        assert err is not None

    def test_empty_dataframe_returned_on_error(self):
        csv = make_csv("ticker,quantity\nAAPL,10\n")
        df, err = parse_csv(csv)
        assert df.empty


class TestInvalidValues:
    def test_invalid_type_value(self):
        csv = make_csv("ticker,quantity,date,price,type\nAAPL,10,2024-01-15,185.50,HOLD\n")
        df, err = parse_csv(csv)
        assert err is not None
        assert "HOLD" in err

    def test_non_numeric_price(self):
        csv = make_csv("ticker,quantity,date,price,type\nAAPL,10,2024-01-15,abc,BUY\n")
        df, err = parse_csv(csv)
        assert err is not None

    def test_non_numeric_quantity(self):
        csv = make_csv("ticker,quantity,date,price,type\nAAPL,ten,2024-01-15,185.50,BUY\n")
        df, err = parse_csv(csv)
        assert err is not None

    def test_extra_columns_ignored(self):
        csv = make_csv(
            "ticker,quantity,date,price,type,notes\n"
            "AAPL,10,2024-01-15,185.50,BUY,first buy\n"
        )
        df, err = parse_csv(csv)
        assert err is None
        assert "notes" not in df.columns

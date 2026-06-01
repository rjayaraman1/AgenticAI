import pandas as pd

REQUIRED = {"ticker", "quantity", "date", "price", "type"}


def parse_csv(file) -> tuple[pd.DataFrame, str | None]:
    try:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip().str.lower()

        missing = REQUIRED - set(df.columns)
        if missing:
            return pd.DataFrame(), f"Missing columns: {', '.join(sorted(missing))}"

        df = df[list(REQUIRED)].copy()
        df["ticker"] = df["ticker"].str.upper().str.strip()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["type"] = df["type"].str.upper().str.strip()

        if df[["quantity", "price"]].isna().any().any():
            return pd.DataFrame(), "Non-numeric values found in quantity or price."

        invalid = ~df["type"].isin(["BUY", "SELL"])
        if invalid.any():
            bad = df[invalid]["type"].unique().tolist()
            return pd.DataFrame(), f"Invalid type values (must be BUY or SELL): {bad}"

        df["source"] = "csv"
        return df, None
    except Exception as exc:
        return pd.DataFrame(), str(exc)

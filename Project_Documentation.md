# Stock Market Analyzer — Project Documentation

---

## Original Prompts

**Prompt 1**
> I want to build a simple stock market analyzer using Python3 for the following requirement

**Prompt 2**
> I want you to create 3 tabs

**Prompt 3**
> In the first tab, the app should allow a CSV file upload with a stock market transaction history and should also have the ability to enter manual transactions

**Prompt 4**
> In the second tab, I want a view of my consolidated portfolio with a pie chart showing portfolio allocation and a stock wise allocation with the following:
> - Current quantity
> - Average cost basis
> - Current prices
> - Profits and other useful details

**Prompt 5**
> In the third tab, show historical performance. Create a metric card with the following metrics:
> - Total lifetime investment
> - Total proceeds from sale
> - Current portfolio value
> - Total returns
> - XIRR
> - Trend line for the portfolio over time

**Prompt 6**
> First brainstorm with me the app creation plan, file structure that you are thinking about and app architecture with me.
> Do not write any code until I give you a go ahead.

---

## Brainstorming & Architecture Decisions

### Tech Stack

| Layer | Tool | Reason |
|---|---|---|
| UI | Streamlit | Fast Python-native multi-tab web app |
| Project management | UV | Modern Python packaging and venv management |
| Market data | yfinance | Free, no API key needed, covers US equities |
| Data wrangling | pandas | Standard for tabular finance data |
| Charts | Plotly | Interactive pie charts and trend lines |
| XIRR calculation | pyxirr | Accurate annualized return on irregular cash flows |

### CSV Schema Discussion

Initial assumption: `ticker, quantity, date, price`

Raised question: CSV has no BUY/SELL type column — two options discussed:
- Option A: Infer from quantity sign (positive = BUY, negative = SELL)
- Option B: Add explicit `type` column to the CSV

**Decision: Add `type` column to CSV (Option B)**

Final confirmed CSV schema:

| Column | Type | Example |
|---|---|---|
| `ticker` | string | `AAPL` |
| `quantity` | float | `10` |
| `date` | date | `2024-01-15` |
| `price` | float | `185.50` |
| `type` | string | `BUY` or `SELL` |

### Tab 1 Design Decision

Manual entry was confirmed to be **separate** from CSV upload (not merged at input time). Both sources feed a single shared ledger tagged with a `source` column (`csv` or `manual`).

### Other Confirmed Decisions

| Area | Decision |
|---|---|
| Tickers | US stocks: AAPL, MSFT, ORCL |
| Currency | USD only |
| State persistence | Streamlit session_state (in-memory, no database) |
| Historical data | yfinance per-ticker history with caching |
| XIRR | Buys = outflows, Sells + current value = inflows |

---

## Final Architecture

### Data Flow

```
CSV Upload / Manual Entry
        │
        ▼
   session_state  ◄──── persists across tab switches
        │
   ┌────┴────────────────────┐
   ▼                         ▼
Tab 2: Portfolio           Tab 3: Performance
   │                         │
   ▼                         ▼
yfinance (current prices)  yfinance (historical OHLC)
   │                         │
   ▼                         ▼
Pie chart + table         Metric cards + trend line
```

### File Structure

```
stock-analyzer/
├── pyproject.toml              # UV project config + pinned dependencies
├── uv.lock                     # Lock file (auto-generated)
├── app.py                      # Streamlit entry point, tab routing
├── data/
│   ├── __init__.py
│   ├── store.py                # session_state CRUD for the transaction ledger
│   └── loader.py               # CSV parser with schema validation
├── finance/
│   ├── __init__.py
│   ├── market.py               # yfinance wrapper with st.cache_data
│   └── calculations.py         # portfolio math, XIRR, metrics, history reconstruction
├── tabs/
│   ├── __init__.py
│   ├── transactions.py         # Tab 1: upload + manual entry + ledger view
│   ├── portfolio.py            # Tab 2: pie chart + stock breakdown table
│   └── performance.py          # Tab 3: metric cards + trend line
└── stock_transactions.csv      # Sample data for testing (AAPL, MSFT, ORCL)
```

---

## Module Responsibilities

### `data/store.py`
Thin wrapper around `st.session_state`. Provides `init()`, `get()`, `add()`, `clear()`.
All tabs read/write through this — no direct session_state access elsewhere.

### `data/loader.py`
Parses uploaded CSV files. Validates required columns, coerces types, enforces BUY/SELL values.
Returns `(DataFrame, error_string)` — caller decides how to show the error.

### `finance/market.py`
Wraps yfinance calls with `@st.cache_data`:
- `get_current_price(ticker)` — last price with 5-minute TTL, falls back to recent history
- `get_prices_bulk(tickers)` — batch current prices
- `get_historical_prices(ticker, start, end)` — per-ticker OHLC with 1-hour TTL
- `get_all_historical_prices(tickers, start, end)` — joins per-ticker series into wide DataFrame

### `finance/calculations.py`
Pure computation, no Streamlit dependencies:
- `compute_portfolio()` — per-ticker qty, avg cost, P&L
- `compute_xirr()` — pyxirr XIRR with buy/sell cash flows
- `compute_metrics()` — aggregate metrics dict for Tab 3
- `compute_historical_portfolio_value()` — vectorized daily portfolio reconstruction

### `tabs/transactions.py`
Two-column layout: CSV upload (left) | Manual entry form (right).
Shared ledger displayed below the divider with row count and source breakdown.

### `tabs/portfolio.py`
Fetches live prices, computes portfolio, renders:
- 4 summary metric cards (value, cost, P&L, open positions)
- Pie chart (Plotly donut) of current value allocation
- Stock-wise breakdown table with formatted currency/percentage columns

### `tabs/performance.py`
Fetches live prices + full historical prices, computes metrics and history, renders:
- 6 metric cards across 2 rows
- Plotly area chart (trend line) with buy/sell markers overlaid

---

## How to Run

```bash
cd stock-analyzer
uv run streamlit run app.py
```

App opens at `http://localhost:8501`.

### Testing with sample data
Upload `stock_transactions.csv` in the Transactions tab.
Contains 8 transactions across AAPL, MSFT, and ORCL spanning 2024–2025.

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| streamlit | >=1.58.0 | UI framework |
| yfinance | >=1.4.1 | Market data |
| pandas | >=3.0.3 | Data manipulation |
| plotly | >=6.7.0 | Interactive charts |
| pyxirr | >=0.10.8 | XIRR calculation |
| numpy | >=2.4.6 | Numerical operations |

# Stock Market Analyzer 

**Date:** May 31 2026
**Tool:** Claude Code (claude-sonnet-4-6)
**Project:** Stock Market Analyzer — Streamlit web app for personal portfolio tracking

---

## 1. Project Overview

The Stock Market Analyzer is a Python web application built using Streamlit that allows an individual investor to track, visualize, and analyze a personal stock portfolio. The app is organized into three tabs, each serving a distinct analytical purpose.

**Tab 1 — Transactions** acts as the data entry layer. Users can either upload a CSV file containing their transaction history or enter trades manually through a form. Both input methods feed into a shared in-memory transaction ledger, tagged by source so the user can distinguish CSV-loaded data from manually entered rows. A clear-all option resets the session.

**Tab 2 — Portfolio** provides a snapshot of current open positions. It fetches live market prices via yfinance and computes per-stock metrics including current quantity held, weighted average cost basis, current market value, and profit/loss in both dollar and percentage terms. A donut pie chart gives an at-a-glance view of how capital is distributed across holdings. Following a feature iteration, the tab also shows annualized volatility and beta (vs S&P 500) for each position, and offers a one-click CSV export of the full breakdown.

**Tab 3 — Performance** provides the historical and return analysis layer. Six metric cards summarize total lifetime investment, proceeds from completed sales, current portfolio value, total returns, and XIRR (an annualized return metric that accounts for the timing of cash flows). Below the metric cards, a portfolio value trend line reconstructs the daily dollar value of the portfolio from the first transaction date to today by replaying transaction history against historical prices. A second chart — added during a feature iteration — overlays the portfolio's indexed performance against the S&P 500 (SPY), both normalized to a base of 100 at the portfolio start date.

The project was set up as a UV-managed Python project, making dependency management and virtual environment handling reproducible and portable. A suite of 41 unit tests covers the data parsing and financial calculation layers.

---

## 2. Datasets Used

### User-Provided Transaction Data
The primary input to the app is a transaction ledger provided by the user, either via CSV upload or manual entry. The expected schema is:

| Column   | Type   | Description                        |
|----------|--------|------------------------------------|
| ticker   | string | Stock symbol (e.g. AAPL, MSFT)     |
| quantity | float  | Number of shares traded            |
| date     | date   | Date of the transaction            |
| price    | float  | Price per share at time of trade   |
| type     | string | BUY or SELL                        |

A sample file (`stock_transactions.csv`) was included with 8 transactions across three US equities — Apple (AAPL), Microsoft (MSFT), and Oracle (ORCL) — spanning January 2024 to January 2025. This file was used for testing all three tabs during development.

### yfinance — Live and Historical Market Data
All market data is sourced from Yahoo Finance via the yfinance Python library. No API key is required. Two types of data are fetched:

- **Current prices** — used in Tab 2 to compute portfolio value and P&L. Fetched via `Ticker.fast_info.last_price` with a 5-minute cache TTL to avoid redundant calls during a session.
- **Historical daily OHLC prices** — used in Tab 3 to reconstruct portfolio value over time and to compute risk metrics (volatility, beta). Fetched with a 1-hour cache TTL.

### S&P 500 Benchmark (SPY)
The SPDR S&P 500 ETF Trust (SPY) is used as the benchmark for the indexed performance comparison chart in Tab 3 and for beta calculations in Tab 2. It is fetched from yfinance alongside the user's own holdings in the same historical data call, adding no extra API overhead.

---

## 3. Prompts Used During Vibe Coding

The app was built through a structured conversational workflow. The prompts below were used in sequence.

**Prompt 1** — High-level intent
> "I want to build a simple stock market analyzer using Python3 for the following requirement"

**Prompt 2** — UI structure
> "I want you to create 3 tabs"

**Prompt 3** — Tab 1 specification
> "In the first tab, the app should allow a CSV file upload with a stock market transaction history and should also have the ability to enter manual transactions"

**Prompt 4** — Tab 2 specification
> "In the second tab, I want a view of my consolidated portfolio with a pie chart showing portfolio allocation and a stock wise allocation with the following: Current quantity, Average cost basis, Current prices, Profits and other useful details"

**Prompt 5** — Tab 3 specification
> "In the third tab, show historical performance. Create a metric card with the following metrics: Total lifetime investment, Total proceeds from sale, Current portfolio value, Total returns, XIRR, Trend line for the portfolio over time"

**Prompt 6** — Brainstorm gate (no code yet)
> "First brainstorm with me the app creation plan, file structure that you are thinking about and app architecture with me. Do not write any code until I give you a go ahead."

**Clarification prompts** (during brainstorming)
- Confirmed CSV schema: ticker, quantity, date, price
- Decided to add an explicit `type` column (BUY/SELL) to the CSV rather than inferring from quantity sign
- Confirmed manual entry should be a separate input, not merged with CSV at upload time
- Confirmed tickers: US stocks (AAPL, MSFT, ORCL)

**Go-ahead prompt**
> "go ahead and create the app"

**Feature iteration prompt**
> "Sure, add your suggestion 1, 3 and 5"
(Benchmark comparison, CSV export, Volatility & Beta — selected from a presented list of 5 suggestions)

**Housekeeping prompts**
- Rename `sample_transactions.csv` to `stock_transactions.csv`
- Save prompts and plan to a Project Documentation file
- Create high-level test cases
- Create this reflection document

---

## 4. Iterations and Refinements

### Iteration 1 — CSV Schema Design
The initial brainstorm assumed the CSV would have four columns: ticker, quantity, date, price. During the brainstorm review, the question of how to represent BUY vs SELL was raised. Two options were considered:

- **Option A:** Infer from quantity sign — positive means BUY, negative means SELL
- **Option B:** Add an explicit `type` column

Option A would have required users to enter negative numbers for sells, which is error-prone and non-obvious. Option B was chosen because it is explicit, readable, and easier to validate programmatically. The CSV loader was built to reject any row where type is not exactly `BUY` or `SELL`.

### Iteration 2 — Manual Entry Scope
The original prompt said "also ability to enter manual transactions" without specifying whether manual entries should integrate with the CSV upload or stand alone. During brainstorming this was clarified: manual entry is a separate form in the same tab, and both sources merge into one shared ledger tagged by origin. This made it easy to later filter or audit which transactions came from where.

### Iteration 3 — Feature Additions (Post-Build)
After the initial app was complete and running, five additional features were proposed. Three were approved and implemented:

**Benchmark Comparison (S&P 500 overlay)**
The initial performance tab showed only the portfolio's dollar value over time. While useful, it gave no context for whether the returns were good or bad relative to the broader market. Adding the indexed comparison chart against SPY gives that context immediately — a line above 100 means you beat the market from that start date, a line below means you did not. This was implemented by including SPY in the same historical price fetch already happening for the portfolio tickers, so it added no extra API call. Both series are normalized to 100 at the portfolio's first transaction date.

**CSV Export**
The portfolio breakdown table in Tab 2 showed all the relevant data but had no way to take it out of the browser. Adding a download button with raw (unformatted) numbers makes the data usable in Excel, Google Sheets, or any downstream tool. The key implementation detail was exporting the raw numeric DataFrame rather than the display-formatted version (which had dollar signs and percentage symbols as strings).

**Risk Metrics — Volatility and Beta**
Adding annualized volatility and beta gives the user a quantitative sense of how risky each position is. Volatility (annualized standard deviation of daily returns) measures absolute price variability. Beta measures how a stock moves relative to the market — a beta above 1 means the stock amplifies market moves, below 1 means it dampens them. Both were computed from 1 year of historical price data already available via yfinance, and merged as two new columns into the existing stock-wise breakdown table.

### Iteration 4 — File Naming
The sample data file was initially named `sample_transactions.csv`. After reviewing the file in the IDE, it was renamed to `stock_transactions.csv` to better reflect what the file actually contains. All references in Project_Documentation.md were updated accordingly.

---

## 5. Learnings and Observations from the Workflow

### The Brainstorm Gate Was the Most Valuable Step
Prompt 6 — "brainstorm with me first, do not write any code until I give you a go ahead" — turned out to be the highest-leverage prompt in the entire session. It forced all ambiguities to surface before any code was written. The CSV schema question, the manual entry scope question, and the ticker assumption were all resolved in the brainstorm phase. If coding had started immediately from Prompt 1–5, those decisions would have been made arbitrarily by the model, and would likely have required rework once the user saw the result. The brainstorm gate cost about five minutes and probably saved thirty.

### Incremental Prompting Produces Better Results Than One Long Prompt
The prompts in this session were layered: high-level intent first, then structure, then tab-by-tab detail, then architecture review, then implementation. This allowed each step to build on confirmed decisions from the previous step. A single mega-prompt asking for the full app upfront would have produced something functional but filled with silent assumptions. The incremental approach meant the user retained control at every fork.

### Vibe Coding Is Most Effective When You Know What You Want
The prompts in this session were specific about outputs (pie chart, metric cards, trend line, XIRR) even if they were not specific about implementation. This gave the model enough direction to make good choices without needing to ask about every detail. Vague prompts like "make a nice dashboard" would have produced something generic. The specificity of the metric card list in Prompt 5 — six named metrics — was directly reflected in the final UI.

### Suggesting Features After the Build Is a Natural Extension Point
Asking "what useful features could you suggest?" after the initial build was complete surfaced ideas that were grounded in what had already been built. The benchmark comparison and risk metrics suggestions both required historical price data that was already being fetched — they were near-zero cost to add. If those features had been in the original spec they might have complicated the initial build; asking for them as a follow-up was cleaner.

### Tests Are Easy to Add When the Logic Is Isolated
The financial calculation functions (`compute_portfolio`, `compute_xirr`, `compute_metrics`, `compute_risk_metrics`) and the CSV parser (`parse_csv`) were written as pure functions with no Streamlit dependencies. This made them trivially testable with pytest — no mocking of session state, no patching of cache decorators. The 41 tests were written and passing in one pass. The separation of concerns between data, finance, and UI layers paid off immediately here.

### Caching Strategy Matters for a Data-Heavy App
The app makes two types of external calls: fast (current price, 5-minute cache) and slow (historical OHLC, 1-hour cache). Without `@st.cache_data`, every tab switch would re-fetch everything from yfinance, making the app sluggish and burning rate limits. The caching design means the first load is slow by design, and subsequent interactions within the session are near-instant. The SPY benchmark data was piggybacked onto the existing historical price call, so the benchmark chart added no noticeable latency.

### XIRR Is the Right Return Metric for Irregular Cash Flows
Simple total return percentage does not account for when money was invested. If you invested $1,000 one year ago and $9,000 last week, a 10% total return means something very different than if you had invested all $10,000 a year ago. XIRR handles this correctly by treating each buy as a dated cash outflow and each sell plus current value as a dated inflow, then finding the annualized rate that makes the net present value of those flows equal to zero. It is a more honest metric than total return percentage for a portfolio built up over time.

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


## Dependencies

| Package | Version | Purpose |
|---|---|---|
| streamlit | >=1.58.0 | UI framework |
| yfinance | >=1.4.1 | Market data |
| pandas | >=3.0.3 | Data manipulation |
| plotly | >=6.7.0 | Interactive charts |
| pyxirr | >=0.10.8 | XIRR calculation |
| numpy | >=2.4.6 | Numerical operations |

## How to Run

```bash
cd stock-analyzer
uv run streamlit run app.py
```

### Asked to write tests:

How to run: uv run streamlit run app.py

App is up and running here: http://localhost:8501/

Asked Claude to write tests :

uv run pytest tests/ -v

*Built with Claude Code (claude-sonnet-4-6) via vibe coding — May 2026*

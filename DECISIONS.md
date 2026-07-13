# Decisions Log

Project decisions and the reasoning behind them, in the order they were made.

## Phase 0 — Setup

- **Repo/venv/folder structure**: git + venv, folders: data/{raw,processed}, notebooks/, src/, tests/
- **Data tracking**: data/raw/ is gitignored (easily re-fetched from API); data/processed/ is tracked (reproducible snapshot of cleaned/feature-engineered data)
- **Notebooks vs scripts**: chose notebooks/ for exploration and interactive learning; reusable code will graduate into src/

## Phase 1 — Pull & explore data

- **Data source**: yfinance — no API key required, simple pandas-friendly interface, good fit for learning without auth/rate-limit overhead
- **Asset**: AAPL — high liquidity, long clean history (no missing data), volatile enough to make later feature engineering meaningful
- **Date range**: 5 years (~1255 trading days), pulled via `ticker.history(period="5y")`

## Phase 2 — Feature engineering

- **Persisted raw data**: saved the yfinance pull to data/raw/aapl.csv so downstream notebooks load from disk instead of re-hitting the API each time.
- **Features built**: daily_return (Close-to-Close % change), ma_20 (20-day rolling mean of Close), volatility_20 (20-day rolling std of daily_return, not raw price), momentum_10 (10-day price % change).
- **NaN handling deferred**: rolling/shift-based features leave leading NaN rows; will drop them when building the train/test dataset in Phase 3 rather than now.


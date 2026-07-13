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

## Phase 3 — Baseline model

- **Target**: binary next-day direction (Close tomorrow > Close today), built via shift(-1); kept an intermediate `next_close` column with real NaN so the final trailing row could be correctly dropped (see LEARNINGS: NaN vs. cast-to-0 gotcha).
- **Train/test split**: chronological 80/20 (not random/shuffled) via `train_test_split(..., shuffle=False)`, to avoid training on future data relative to the test set.
- **Model**: LogisticRegression, default settings, trained on 4 features (daily_return, ma_20, volatility_20, momentum_10).
- **Feature scaling**: added StandardScaler (fit on train only, applied to test) after the unscaled model collapsed to always predicting the majority class.
- **Result**: ~52.6% accuracy even after scaling, with the model still nearly always predicting "up" — essentially no real signal from these 4 simple technical features for next-day direction. Documented as an honest baseline result rather than iterated on further; revisit feature set/target definition in a later phase if desired.


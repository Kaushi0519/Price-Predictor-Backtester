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


## Phase 4 — Random forest vs. baseline

- **Model**: RandomForestClassifier, n_estimators=100, max_depth=5, random_state=42, trained on the same 4 features/target/split as the Phase 3 baseline (unscaled — tree splits are threshold-based, not sensitive to feature scale).
- **Result**: train accuracy 72.8% vs. test accuracy 48.6% — a large gap indicating overfitting, and test accuracy actually below both the logistic regression baseline (52.6%) and a coin flip.
- **Feature importances**: nearly evenly split across all 4 features (0.23–0.29 each), no standout predictor — reinforces that the bottleneck is weak signal in the feature set itself, not model choice.
- **Conclusion**: did not pursue further hyperparameter tuning here — added model complexity amplified noise-fitting rather than finding real signal. Documented as a learning outcome; future improvement should focus on richer features or a different target definition, not a more powerful model.


## Phase 5 — Backtesting engine

- **Model used**: Phase 3's logistic regression baseline (not the overfit random forest) — using known-noisy predictions would make backtest results meaningless.
- **Return alignment**: built `next_day_return` = (next_close - Close) / Close, explicitly the forward-looking T→T+1 return, instead of the already-realized `daily_return` column — avoids a subtle misalignment bug where the backtest would score a return that happened before the prediction was made.
- **Strategy logic**: simple long/cash — hold the stock on days predicted "up" (capture actual_return), sit in cash on days predicted "down" (capture 0). Implemented via `prediction * actual_return` rather than an if/else, since prediction is already 0/1.
- **Transaction costs**: modeled as a flat 0.1% per trade, applied only on days where the prediction flipped from the previous day (detected via `.diff()`).
- **Result**: strategy ~49.45% return before costs, ~48.86% after costs (4 trades total, so costs barely mattered) — nearly matching buy-and-hold, consistent with the model's Phase 3/4 finding that it carries no real predictive signal for next-day direction.

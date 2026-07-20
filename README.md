# Price Predictor & Backtester

Predicting next-day stock price direction (AAPL) and backtesting a simple trading strategy built on those predictions. Built to get hands-on with pandas, NumPy, scikit-learn, time-series ML pitfalls, backtesting, and Docker — not to produce a profitable trading system.

## What's actually in here

1. **Data pull** — 5 years of AAPL price history via `yfinance` (no API key required).
2. **Feature engineering** — daily returns, a 20-day moving average, 20-day rolling volatility (std of returns, not raw price), and 10-day momentum.
3. **Baseline model** — logistic regression predicting next-day up/down, with a chronological (not shuffled) train/test split.
4. **Random forest** — a second model compared against the baseline.
5. **Backtesting engine** — simulates trading on the baseline model's predictions, including transaction costs, compared against buy-and-hold.
6. *(Phase 6, LLM news sentiment, was scoped out — see `DECISIONS.md` for why.)*
7. **Docker** — the trained-baseline-model + backtest logic consolidated into `src/run_backtest.py`, containerized so it runs anywhere with one command.

## Result

This didn't work to great effect — the features tested here (returns, moving average, volatility, momentum) didn't give the models much to work with:

- Logistic regression baseline: ~52.6% test accuracy, barely above a coin flip, mostly just predicting "up" every day.
- Random forest: 72.8% train accuracy vs. 48.6% test accuracy — overfit rather than found real structure.
- Backtest: strategy return (~48.86% after transaction costs) nearly matches plain buy-and-hold.

Full reasoning for each result is in `DECISIONS.md`; the underlying concepts (why time-series splits can't shuffle, what overfitting looks like, why backtests can mislead) are in `LEARNINGS.md`.

## Project structure

```
data/
  raw/         # pulled from yfinance, gitignored (easily re-fetched)
  processed/   # cleaned + feature-engineered CSV, tracked in git
notebooks/     # the actual step-by-step exploration, one notebook per phase
src/
  run_backtest.py  # consolidated script: load features -> train baseline model -> run backtest
Dockerfile       # containerizes src/run_backtest.py
DECISIONS.md     # project decisions and the reasoning behind them
LEARNINGS.md     # concepts learned, in plain language
```

## Running it

**Option 1 — step through the notebooks** (the actual learning path, run in order):
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
jupyter notebook
```
Then open `notebooks/01_data_pull.ipynb` through `05_backtester.ipynb` in order — each depends on data/state produced by the previous ones.

**Option 2 — just get the backtest result, via Docker:**
```
docker build -t price-predictor .
docker run price-predictor
```
This runs `src/run_backtest.py` directly against the already-committed `data/processed/aapl_features.csv` — no API calls, no notebook, just the final strategy-vs-buy-and-hold comparison.

## Tech stack

pandas, NumPy, scikit-learn, yfinance, matplotlib, Jupyter, Docker.

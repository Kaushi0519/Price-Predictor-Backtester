# Learnings

Concepts learned along the way, written in my own words.

## Phase 0 — Setup

- git init
- Git ignore:
    - Tells git which files/folders to not track
    - Don't want to track virtual environments, APIs
- Create a virtual environment:
    - Python packages (pandas, scikit-learn, etc.) get installed somewhere on your system. If you install different versions for different projects, they can conflict — project A needs pandas 1.5, project B needs pandas 2.1, and installing globally means only one wins. A virtual environment is an isolated folder with its own Python interpreter and its own package installs, scoped to just this project.
- Create project folder structure:
    - Then stage and commit them:
        - git status
        - git add .
        - git commit "some sort of comment"
- Create GitHub repo:
    - push to github

## Phase 1 — Pull & explore data

- **APIs for data pulls**: instead of manually downloading a CSV, a library like `yfinance` calls Yahoo Finance's endpoints directly and hands back a ready-to-use pandas DataFrame. No API key was needed because yfinance uses Yahoo's public, unauthenticated endpoints (as opposed to something like Alpha Vantage, which requires a registered key).
- **Jupyter notebooks**: cell-based execution means state (variables, loaded data) persists between cells, so I can inspect a DataFrame, plot it, and tweak just one step without re-running the whole script or re-fetching data from the API. This makes it well suited to exploratory work, versus a plain `.py` script that runs top-to-bottom with no easy mid-run inspection.
- **DataFrame vs. Series**: `df['Close']` pulls out a single column as a pandas **Series** (a 1-D labeled array), while `df[['Close']]` (double brackets) would return a one-column **DataFrame**. Both support methods like `.plot()`, which is why the single-bracket version worked directly for plotting.
- **DatetimeIndex**: because yfinance sets the Date column as the DataFrame's index (a `DatetimeIndex`), `.plot()` automatically used it for the x-axis with no extra configuration.
- **Standard deviation vs. variance**: variance is the average squared deviation from the mean (units are squared, e.g. dollars², which isn't intuitive); standard deviation is the square root of variance, bringing it back to the original units (dollars), which is why `std` is the number people actually read.
- **Price std vs. returns std ("volatility")**: the standard deviation of raw closing *price* over 5 years (~$45) mostly reflects AAPL's long-term upward trend, not day-to-day choppiness. A proper volatility measure uses the standard deviation of *daily returns* over a rolling window instead — that isolates short-term noise from long-term drift. We'll build that in Phase 2.


## Phase 2 — Feature engineering

- **Vectorized operations vs. loops**: pandas/NumPy operations act on an entire column at once instead of looping row-by-row in Python. The looping still happens, but underneath in fast compiled code, not slow Python-level iteration. `.shift()`, `.rolling()`, and arithmetic on whole columns are all vectorized.
- **`.shift(N)`**: moves a column's values down by N rows, so row *i* holds what used to be at row *i-N*. Used to compare "today" against "N days ago" without a loop — the basis for daily_return (shift 1) and momentum_10 (shift 10).
- **`.rolling(window=N)`**: creates a sliding window of N consecutive rows that moves forward one row at a time; you then apply an aggregation like `.mean()` or `.std()` to each window. The first N-1 rows are NaN because there aren't enough prior rows yet to fill a full window.
- **`df['col']` vs. `df.col`**: bracket notation looks up a column by name (like a dictionary key) — needed because column names are just data, not something Python knows about ahead of time. Dot notation is for built-in DataFrame methods/attributes (`.head()`, `.shape`) that pandas defines on every DataFrame. `df.col` also works as a shortcut for columns with simple names, but breaks for names with spaces/special characters, so bracket notation is the safer default.
- **Volatility on returns, not price**: standard deviation of raw Close price mostly reflects long-term price drift (e.g. AAPL trending up over 5 years), not actual day-to-day choppiness. Computing rolling std on daily_return instead isolates short-term noise from the long-term trend, giving a more meaningful volatility measure.
- **Data persistence pattern**: pulling from an API is slow and rate-limited; saving one snapshot to data/raw/ and having every downstream notebook load from that CSV instead keeps things fast and makes results reproducible (same data every run, not whatever the API happens to return that day).


## Phase 3 — Baseline model

- **Building a forward-looking target**: `.shift(-1)` moves values *up* by one row (instead of `.shift(1)`, which moves them down), letting you compare "today" to "tomorrow" without a loop. The very last row ends up NaN since there's no tomorrow for it.
- **The NaN-vs-cast-to-0 gotcha**: once a comparison result is cast with `.astype(int)`, any NaN comparison (which evaluates to False) silently becomes a real-looking `0` — indistinguishable from an honest "down" day. To filter these rows out correctly, you have to `dropna()` based on the original NaN-containing column (like `next_close`) *before* casting, not after.
- **Why time-series splits can't shuffle**: real trading only ever uses past data to predict the future, so a random shuffle risks training on rows that are chronologically after your test rows — data leakage from the future. Shuffling also puts near-identical, highly autocorrelated neighboring days on both sides of the split, making the test set less "unseen" than it looks. `train_test_split(..., shuffle=False)` preserves chronological order instead.
- **Logistic regression, conceptually**: fits weights on the input features, passes the weighted sum through a sigmoid function to get a probability between 0 and 1, and classifies based on whether that probability crosses 0.5. Despite the name, it's used for classification, not regression.
- **Accuracy vs. precision vs. recall**: accuracy alone can be misleading if one class is more common — a model that always predicts the majority class can score deceptively well on accuracy while learning nothing. Precision asks "of predicted positives, how many were right?"; recall asks "of actual positives, how many did we catch?" The confusion matrix is the raw breakdown both are calculated from, and is the most honest single view of what a model is actually doing.
- **Feature scaling with StandardScaler**: transforms each feature to mean 0, std 1, so features on very different raw scales (e.g. `ma_20` in the hundreds vs. `daily_return` as small decimals) get treated fairly by the model's regularization. Must `fit_transform` on training data only, then `transform` (not re-fit) on test data — fitting the scaler on the full dataset would leak test-set statistics into training, the same category of mistake as shuffling.
- **A model can "converge" and still be useless**: our logistic regression trained without any warning, but collapsed to predicting the majority class almost every time — accuracy and recall looked fine in isolation, but the confusion matrix revealed it wasn't actually discriminating between up/down days at all.
- **Why the result was weak, and that's okay**: with only 4 simple technical features, the model found close to no real signal for next-day direction — consistent with the efficient market hypothesis, which suggests publicly available price/volume patterns get priced in quickly and shouldn't reliably predict short-term direction. An honest weak baseline is more useful than a falsely impressive one, and sets a real bar for Phase 4 to try to beat.




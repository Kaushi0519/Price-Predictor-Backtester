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


## Phase 4 — Random forest vs. baseline

- **Random forest, conceptually**: an ensemble of many decision trees, each trained on a random subset of rows (bagging) and features, with predictions combined by majority vote. Averaging over many differently-trained trees smooths out individual trees' mistakes/noise.
- **Decision trees and overfitting**: an unconstrained tree keeps splitting until leaves contain very few (or single) training rows, effectively memorizing training data — including its noise — rather than learning a generalizable rule. `max_depth` and similar hyperparameters cap how deep trees can grow to prevent this.
- **The overfitting tell**: a large gap between training accuracy and test accuracy (72.8% vs. 48.6% here) means the model learned patterns specific to the training set that don't hold up on new data — high train performance alone proves nothing about real-world usefulness.
- **More model complexity isn't a fix for weak features**: when there's little genuine signal in the inputs, a more flexible model doesn't find more truth — it finds more noise to fit to. Our forest actually performed worse than the simpler logistic regression baseline, because the added flexibility mostly went toward overfitting rather than capturing real structure.
- **Feature importances**: `.feature_importances_` shows how much each feature contributed to the forest's splits. A near-even split across all features (rather than one dominant one) suggests none of them carries a strong individual signal — a useful diagnostic tool tree-based models give you that logistic regression doesn't as directly.


## Phase 5 — Backtesting engine

- **Return alignment is a real bug risk**: a prediction on day T forecasts the T→T+1 return, not day T's own (already-realized) return. Naively multiplying a prediction by the already-known `daily_return` column would score the backtest on the wrong, already-past return — not technically future-peeking, but an equally serious correctness bug.
- **Vectorized conditional logic via multiplication**: since `prediction` is strictly 0/1, `prediction * actual_return` acts as an if/else switch without writing a loop or an explicit conditional — 1 keeps the value, 0 zeroes it out.
- **`.cumprod()` vs `.cumsum()` for returns**: returns compound (each day's gain/loss applies to the current running balance, not the original principal), so cumulative performance needs `(1 + daily_return).cumprod()`, not a simple running sum — summing would give a misleading result over any multi-day period.
- **A backtest can confirm a bad finding, not just reveal a new one**: since the model almost always predicted "up," the backtest nearly matched buy-and-hold — that's not evidence of skill, it's the same "no real signal" conclusion from Phase 3/4, now visible in return-curve form. Important not to mistake "close to a naive benchmark" for "pretty good" without checking why.
- **Transaction costs via `.diff()`**: `.diff()` gives the difference between each row and the one before it; for a 0/1 prediction column, a nonzero diff means the position changed (a trade happened) that day. Costs only matter meaningfully for strategies that trade frequently — a near-buy-and-hold strategy barely feels them.


## Phase 7 — Docker

- **The problem Docker solves**: "works on my machine" — a script that depends on a specific Python version and package versions can break on a different machine, or the same machine a year later with different versions installed. Docker packages code + runtime + dependencies together so it runs identically anywhere Docker is installed.
- **Image vs. container**: an image is the frozen, packaged blueprint (built once from a Dockerfile); a container is a running instance of that image — same relationship as a class and an object.
- **Dockerfile as a layered recipe**: each instruction (`FROM`, `WORKDIR`, `COPY`, `RUN`, `CMD`) adds a cached layer. Reordering instructions so rarely-changing steps (installing dependencies) come before frequently-changing ones (copying code) means rebuilds after a small code edit don't redo the slow parts.
- **`RUN` vs `CMD`**: `RUN` executes during the *build* and bakes its result into the image (e.g., installing packages once); `CMD` is the command that runs when a container *starts* — it's what makes "runs with one command" possible.
- **Notebooks vs. scripts for deployment**: notebooks are great for interactive exploration but awkward to run headlessly/reproducibly. Consolidating already-understood model + backtest logic into a plain `.py` script with functions and an `if __name__ == "__main__":` entrypoint made it something Docker (or anything else) could run as one clean unit.
- **Containers don't need internet by default**: since our script reads from an already-committed CSV instead of calling the yfinance API live, the container never needs network access to produce a result — a real pattern (bake in what you can, don't assume outside services are reachable).
- **Docker's origins**: built by Solomon Hykes in 2013 on top of Linux kernel features that already existed (namespaces for isolating what a process can see, cgroups for limiting its resource usage). Docker's contribution was making those primitives easy to use via a simple CLI and the Dockerfile format — not inventing isolation itself. It became the de facto standard fast because it solved a universal pain point with a low barrier to entry, similar to how git became the default for version control without being part of any language.
- **Same pattern scales up**: a single containerized script and a full multi-service production app (web server + database + cache, each in its own container, coordinated by tools like `docker-compose` or Kubernetes) are the same underlying idea at different scale — one command in, one portable, reproducible result out.




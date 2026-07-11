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




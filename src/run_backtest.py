import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

FEATURE_COLS = ["daily_return", "ma_20", "volatility_20", "momentum_10"]
TRANSACTION_COST = 0.001  # 0.1% per trade


def load_features(path="data/processed/aapl_features.csv"):
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    df["next_close"] = df["Close"].shift(-1)
    df["target"] = (df["next_close"] > df["Close"]).astype(int)
    df["next_day_return"] = (df["next_close"] - df["Close"]) / df["Close"]
    return df.dropna(subset=FEATURE_COLS + ["next_close"])


def train_baseline_model(model_df):
    X = model_df[FEATURE_COLS]
    y = model_df["target"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression()
    model.fit(X_train_scaled, y_train)

    predictions = model.predict(X_test_scaled)
    return X_test, predictions


def run_backtest(model_df, X_test, predictions):
    test_returns = model_df.loc[X_test.index, "next_day_return"]

    backtest_df = pd.DataFrame(
        {"prediction": predictions, "actual_return": test_returns.values},
        index=X_test.index,
    )

    backtest_df["strategy_return"] = backtest_df["prediction"] * backtest_df["actual_return"]
    backtest_df["trade"] = backtest_df["prediction"].diff().fillna(0) != 0
    backtest_df["strategy_return_after_costs"] = (
        backtest_df["strategy_return"] - backtest_df["trade"] * TRANSACTION_COST
    )

    backtest_df["cumulative_strategy"] = (1 + backtest_df["strategy_return"]).cumprod()
    backtest_df["cumulative_strategy_after_costs"] = (
        1 + backtest_df["strategy_return_after_costs"]
    ).cumprod()
    backtest_df["cumulative_buy_hold"] = (1 + backtest_df["actual_return"]).cumprod()

    return backtest_df


def main():
    model_df = load_features()
    X_test, predictions = train_baseline_model(model_df)
    backtest_df = run_backtest(model_df, X_test, predictions)

    strategy_return = (backtest_df["cumulative_strategy"].iloc[-1] - 1) * 100
    strategy_return_after_costs = (backtest_df["cumulative_strategy_after_costs"].iloc[-1] - 1) * 100
    buy_hold_return = (backtest_df["cumulative_buy_hold"].iloc[-1] - 1) * 100
    num_trades = int(backtest_df["trade"].sum())

    start_date = str(backtest_df.index[0])[:10]
    end_date = str(backtest_df.index[-1])[:10]
    print(f"Test period: {start_date} to {end_date}")
    print(f"Number of trades: {num_trades}")
    print(f"Strategy return (no costs):   {strategy_return:.2f}%")
    print(f"Strategy return (with costs): {strategy_return_after_costs:.2f}%")
    print(f"Buy & hold return:            {buy_hold_return:.2f}%")


if __name__ == "__main__":
    main()

import pandas as pd


def load_backtest_data(
    path
):

    df = pd.read_csv(
        path
    )

    if "Date" in df.columns:

        df["Date"] = pd.to_datetime(
            df["Date"]
        )

    return df
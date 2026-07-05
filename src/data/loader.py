import pandas as pd


def load_raw_data(path):

    return pd.read_csv(
        path,
        parse_dates=["Date"]
    )
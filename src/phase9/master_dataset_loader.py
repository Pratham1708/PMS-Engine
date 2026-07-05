import pandas as pd

def save_dataset(

    df,

    path
):

    df.to_csv(

        path,

        index=False
    )

def load_dataset(
    path
):

    return pd.read_csv(
        path
    )


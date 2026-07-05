import pandas as pd

def dataset_report(df):

    report = {

        "Rows":
        len(df),

        "Stocks":
        df["Symbol"].nunique(),

        "Start":
        df["Date"].min(),

        "End":
        df["Date"].max()
    }

    return pd.DataFrame(
        report,
        index=[0]
    )
    
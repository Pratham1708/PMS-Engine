import pandas as pd

def market_breadth(
    scanner_df
):

    return pd.DataFrame(

        scanner_df[
            "Signal"
        ].value_counts()
    )
import pandas as pd
def scanner_summary(df):

    return pd.DataFrame(

        df[
            "Signal"
        ]

        .value_counts()
    )
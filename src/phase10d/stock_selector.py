def select_buy_candidates(df):

    return (

        df[
            df["SignalV2"] == "BUY"
        ]

        .copy()

        .reset_index(
            drop=True
        )
    )
def rank_stocks(df):

    return (

        df

        .sort_values(

            "CompositeScore",

            ascending=False
        )

        .reset_index(
            drop=True
        )
    )
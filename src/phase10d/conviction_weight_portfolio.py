def conviction_weight_portfolio(

    buy_df,

    top_n=5
):

    portfolio = buy_df.head(
        top_n
    ).copy()

    total_score = (

        portfolio[
            "CompositeScoreV2"
        ].sum()
    )

    portfolio["Weight"] = (

        portfolio[
            "CompositeScoreV2"
        ]

        /

        total_score

        * 100
    )

    return portfolio
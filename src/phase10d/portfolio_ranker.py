def rank_portfolio_candidates(
    df
):

    return (

        df

        .sort_values(

            "CompositeScoreV2",

            ascending=False

        )

        .reset_index(drop=True)

    )
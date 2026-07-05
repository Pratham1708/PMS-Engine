def equal_weight_portfolio(

    buy_df,

    top_n=5
):

    portfolio = buy_df.head(
        top_n
    ).copy()

    portfolio["Weight"] = (

        100 / len(portfolio)
    )

    return portfolio
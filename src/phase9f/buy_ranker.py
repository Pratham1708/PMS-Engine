def top_buys(
    scanner_df,
    n=10
):

    return scanner_df.sort_values(

        "CompositeScore",

        ascending=False

    ).head(n)
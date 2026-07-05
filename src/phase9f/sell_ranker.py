def top_sells(
    scanner_df,
    n=10
):

    return scanner_df.sort_values(

        "CompositeScore",

        ascending=True

    ).head(n)
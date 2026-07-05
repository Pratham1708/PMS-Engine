def top_opportunities(
    results_df,
    top_n=10
):

    return results_df.sort_values(

        "Confidence",

        ascending=False

    ).head(top_n)
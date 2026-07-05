def calculate_reliability(similar_df):

    returns = similar_df["FutureReturn"]

    return {

        "Occurrences": len(returns),

        "WinRate":
        (returns > 0).mean(),

        "AverageReturn":
        returns.mean(),

        "MedianReturn":
        returns.median(),

        "BestReturn":
        returns.max(),

        "WorstReturn":
        returns.min()
    }
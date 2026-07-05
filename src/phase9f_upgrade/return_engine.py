def estimate_return(row):

    score = 0

    score += (

        row["Price_vs_EMA20"] - 1
    ) * 100

    score += (

        row["Price_vs_EMA50"] - 1
    ) * 100

    score += (

        row["Price_vs_EMA200"] - 1
    ) * 100

    return score / 3
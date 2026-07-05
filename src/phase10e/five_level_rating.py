import pandas as pd


def generate_five_level_rating(
    df,
    score_col="CompositeScoreV2"
):

    df = df.copy()

    strong_buy = df[score_col].quantile(0.90)

    buy = df[score_col].quantile(0.70)

    sell = df[score_col].quantile(0.30)

    strong_sell = df[score_col].quantile(0.10)

    def mapper(score):

        if score >= strong_buy:
            return "STRONG BUY"

        elif score >= buy:
            return "BUY"

        elif score <= strong_sell:
            return "STRONG SELL"

        elif score <= sell:
            return "SELL"

        else:
            return "HOLD"

    df["FinalRating"] = df[
        score_col
    ].apply(mapper)

    return df
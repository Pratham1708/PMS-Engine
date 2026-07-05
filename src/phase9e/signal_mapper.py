def map_signal(
    composite_score
):

    if composite_score >= 70:

        return "STRONG BUY"

    elif composite_score >= 30:

        return "BUY"

    elif composite_score > -30:

        return "HOLD"

    elif composite_score > -70:

        return "SELL"

    return "STRONG SELL"
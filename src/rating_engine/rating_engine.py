def technical_rating(
    score
):

    if score >= 60:

        return "STRONG BUY"

    elif score >= 20:

        return "BUY"

    elif score > -20:

        return "HOLD"

    elif score > -60:

        return "SELL"

    else:

        return "STRONG SELL"
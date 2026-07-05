def technical_rating(
    technical_score
):

    if technical_score <= -60:

        return "STRONG SELL"

    elif technical_score <= -20:

        return "SELL"

    elif technical_score < 20:

        return "HOLD"

    elif technical_score < 60:

        return "BUY"

    else:

        return "STRONG BUY"
def signal_from_score(
    score
):

    if score >= 30:

        return "BUY"

    elif score <= -30:

        return "SELL"

    else:

        return "HOLD"
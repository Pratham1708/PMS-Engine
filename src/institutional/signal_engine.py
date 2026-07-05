def institutional_signal(

    score

):

    if score >= 80:

        return "STRONG BUY"

    elif score >= 65:

        return "BUY"

    elif score >= 40:

        return "HOLD"

    elif score >= 20:

        return "SELL"

    else:

        return "STRONG SELL"
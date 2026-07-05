def historical_signal(
    future_return
):

    if future_return >= 0.08:

        return "STRONG BUY"

    elif future_return >= 0.03:

        return "BUY"

    elif future_return > -0.03:

        return "HOLD"

    elif future_return > -0.08:

        return "SELL"

    else:

        return "STRONG SELL"
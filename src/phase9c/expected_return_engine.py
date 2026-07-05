def expected_return_signal(
    expected_return
):

    if expected_return >= 5:

        return "STRONG BUY"

    elif expected_return >= 2:

        return "BUY"

    elif expected_return > -2:

        return "HOLD"

    elif expected_return > -5:

        return "SELL"

    return "STRONG SELL"
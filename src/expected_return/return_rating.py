def return_signal(
    expected_return
):

    pct = expected_return * 100

    if pct >= 4:

        return "STRONG BUY"

    elif pct >= 2:

        return "BUY"

    elif pct > -2:

        return "HOLD"

    elif pct > -4:

        return "SELL"

    else:

        return "STRONG SELL"

def return_strength(
    expected_return
):

    pct = abs(
        expected_return * 100
    )

    if pct >= 5:

        return "HIGH"

    elif pct >= 2:

        return "MEDIUM"

    return "LOW"


def generate_signal(

    probabilities,

    expected_return,

    confidence

):

    long_prob = probabilities.get(
        "LONG",
        0
    )

    short_prob = probabilities.get(
        "SHORT",
        0
    )

    if (

        long_prob > 0.55

        and

        expected_return > 0.01

        and

        confidence > 60

    ):

        return "BUY"

    if (

        short_prob > 0.55

        and

        expected_return < -0.01

        and

        confidence > 60

    ):

        return "SELL"

    return "HOLD"
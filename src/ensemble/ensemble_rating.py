def ensemble_signal(

    probabilities,

    class_names
):

    prob_dict = dict(

        zip(
            class_names,
            probabilities
        )
    )

    long_prob = prob_dict.get(
        "LONG",
        0
    )

    hold_prob = prob_dict.get(
        "HOLD",
        0
    )

    short_prob = prob_dict.get(
        "SHORT",
        0
    )

    max_prob = max(
        long_prob,
        hold_prob,
        short_prob
    )

    if long_prob == max_prob:

        if long_prob >= 0.70:

            return "STRONG BUY"

        elif long_prob >= 0.55:

            return "BUY"

        else:

            return "HOLD"

    if short_prob == max_prob:

        if short_prob >= 0.70:

            return "STRONG SELL"

        elif short_prob >= 0.55:

            return "SELL"

        else:

            return "HOLD"

    return "HOLD"

def confidence_score(

    probabilities
):

    highest = max(
        probabilities
    )

    return round(
        highest * 100,
        2
    )
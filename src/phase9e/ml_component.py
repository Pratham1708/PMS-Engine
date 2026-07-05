def ml_component(
    probabilities
):

    long_prob = probabilities.get(
        "LONG",
        0
    )

    short_prob = probabilities.get(
        "SHORT",
        0
    )

    ml_score = (

        long_prob

        -

        short_prob
    )

    return max(
        -100,
        min(
            100,
            ml_score
        )
    )
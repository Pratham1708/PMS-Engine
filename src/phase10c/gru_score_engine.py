def calculate_gru_score(
    probs
):

    hold = probs[0] * 100

    long = probs[1] * 100

    short = probs[2] * 100

    score = (

        long
        -
        short
    )

    return round(
        score,
        2
    )
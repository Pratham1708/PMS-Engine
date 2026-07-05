def probability_dict(
    probs
):

    return {

        "HOLD":
            probs[0] * 100,

        "LONG":
            probs[1] * 100,

        "SHORT":
            probs[2] * 100
    }
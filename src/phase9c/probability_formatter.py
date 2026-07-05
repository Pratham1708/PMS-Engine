def get_ml_signal(
    probs
):

    return max(
        probs,
        key=probs.get
    )
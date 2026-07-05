def map_signal(
    probabilities
):

    labels = [

        "HOLD",

        "LONG",

        "SHORT"
    ]

    idx = probabilities.argmax()

    return labels[idx]
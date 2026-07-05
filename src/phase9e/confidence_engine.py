def calculate_confidence(
    probabilities
):

    probs = sorted(
        probabilities.values(),
        reverse=True
    )

    top = probs[0]

    second = probs[1]

    confidence = top + (
        top - second
    )

    confidence = min(
        confidence,
        100
    )

    return round(
        confidence,
        2
    )
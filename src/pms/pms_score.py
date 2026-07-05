def calculate_pms_score(
    trend,
    momentum,
    risk,
    confidence
):

    score = (
        trend * 0.30
        +
        momentum * 0.25
        +
        risk * 0.20
        +
        confidence * 0.25
    )

    return round(score,2)
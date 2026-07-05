def confidence_score(
    ml_accuracy,
    reliability,
    adx
):

    score = (
        ml_accuracy * 100 * 0.4
        +
        reliability * 100 * 0.4
        +
        min(adx,50) * 0.2
    )

    return round(score,2)
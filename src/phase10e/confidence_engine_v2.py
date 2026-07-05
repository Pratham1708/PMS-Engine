def confidence_v2(
    composite_score
):

    confidence = abs(
        composite_score
    )

    confidence = max(
        0,
        min(
            confidence,
            100
        )
    )

    return round(
        confidence,
        2
    )
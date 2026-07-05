def calculate_composite_score(

    technical_score,

    ml_score,

    return_score,

    reliability_score
):

    composite = (

        0.40 * technical_score +

        0.30 * ml_score +

        0.20 * return_score +

        0.10 * reliability_score
    )

    return round(
        composite,
        2
    )
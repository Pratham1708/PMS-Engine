def composite_score_v2(

    technical,

    ml,

    expected_return,

    reliability
):

    score = (

        0.35 * technical

        +

        0.30 * ml

        +

        0.20 * expected_return

        +

        0.15 * reliability
    )

    return round(
        score,
        2
    )
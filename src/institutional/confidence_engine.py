def final_confidence(

    agreement,

    reliability,

    ml_confidence

):

    score = (

        agreement * 0.4

        +

        reliability * 100 * 0.3

        +

        ml_confidence * 0.3
    )

    return round(
        score,
        2
    )
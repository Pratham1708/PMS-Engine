def investing_rating(
    technical_score,
    ml_score,
    composite_score
):

    if composite_score >= 70:

        institutional = "STRONG BUY"

    elif composite_score >= 30:

        institutional = "BUY"

    elif composite_score > -30:

        institutional = "HOLD"

    elif composite_score > -70:

        institutional = "SELL"

    else:

        institutional = "STRONG SELL"

    return {

        "Technical": technical_score,

        "AI": ml_score,

        "Institutional": institutional

    }
def confidence_score(

    top_probability,

    reliability,

    expected_return,

    regime

):

    score = 0

    score += top_probability * 50

    score += reliability * 30

    score += min(
        abs(expected_return) * 100,
        10
    )

    if regime in [

        "Bull Market",

        "Bear Market"
    ]:

        score += 10

    return round(
        min(score,100),
        2
    )
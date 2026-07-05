def combine_ratings(

    technical_score,

    probabilities
):

    hold_prob = probabilities["HOLD"]

    long_prob = probabilities["LONG"]

    short_prob = probabilities["SHORT"]

    ml_score = (

        long_prob -

        short_prob
    )

    final_score = (

        0.6 * technical_score +

        0.4 * ml_score
    )

    return final_score
def combine_signals(

    technical_score,

    probs
):

    ml_score = (

        probs["LONG"]

        -

        probs["SHORT"]
    )

    final_score = (

        0.6 * technical_score

        +

        0.4 * ml_score
    )

    if final_score <= -60:

        return "STRONG SELL"

    elif final_score <= -20:

        return "SELL"

    elif final_score < 20:

        return "HOLD"

    elif final_score < 60:

        return "BUY"

    else:

        return "STRONG BUY"
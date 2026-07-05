def build_report(

    symbol,

    technical,

    ml_signal,

    final_signal,

    confidence,

    probs
):

    return {

        "Stock":
        symbol,

        "Technical":
        technical,

        "ML Signal":
        ml_signal,

        "Final Signal":
        final_signal,

        "Confidence":
        confidence,

        "LONG":
        probs["LONG"],

        "HOLD":
        probs["HOLD"],

        "SHORT":
        probs["SHORT"]
    }
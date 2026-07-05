def recommendation(
    probabilities,
    reliability_metrics
):

    top_signal = max(
        probabilities,
        key=probabilities.get
    )

    confidence = probabilities[
        top_signal
    ]

    if confidence < 0.50:

        return "HOLD"

    if (
        top_signal == "LONG"
        and
        reliability_metrics["WinRate"]
        > 0.55
    ):
        return "LONG"

    if (
        top_signal == "SHORT"
        and
        reliability_metrics["WinRate"]
        < 0.45
    ):
        return "SHORT"

    return "HOLD"
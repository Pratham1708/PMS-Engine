def explain(
    recommendation,
    probabilities,
    reliability,
    expected_return,
    risk
):

    text = []

    text.append(
        f"Signal: {recommendation}"
    )

    text.append(
        f"Expected Return: "
        f"{expected_return:.2%}"
    )

    text.append(
        f"Historical Win Rate: "
        f"{reliability['WinRate']:.2%}"
    )

    text.append(
        f"Risk Level: {risk}"
    )

    text.append(
        "Probability Breakdown:"
    )

    for k,v in probabilities.items():

        text.append(
            f"{k}: {v:.2%}"
        )

    return "\n".join(text)
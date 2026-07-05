def reliability_rating(
    win_rate
):

    if win_rate >= 70:

        return "HIGH"

    elif win_rate >= 50:

        return "MEDIUM"

    return "LOW"
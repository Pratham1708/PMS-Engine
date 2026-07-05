def recommendation(score):

    if score >= 80:
        return "STRONG LONG"

    elif score >= 65:
        return "LONG"

    elif score >= 45:
        return "HOLD"

    elif score >= 30:
        return "SHORT"

    else:
        return "STRONG SHORT"
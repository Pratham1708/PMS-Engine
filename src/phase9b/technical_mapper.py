def technical_rating(score):

    if score <= -60:
        return "STRONG SELL"

    elif score <= -20:
        return "SELL"

    elif score < 20:
        return "HOLD"

    elif score < 60:
        return "BUY"

    return "STRONG BUY"
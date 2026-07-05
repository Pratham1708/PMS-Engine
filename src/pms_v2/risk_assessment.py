def assess_risk(
    row
):

    atr_pct = (
        row["ATR14"]
        /
        row["Close"]
    ) * 100

    if atr_pct < 2:

        return "LOW"

    elif atr_pct < 4:

        return "MEDIUM"

    else:

        return "HIGH"
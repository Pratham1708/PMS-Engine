def volatility_score(
    row
):

    atr_pct = (

        row["ATR14"]

        /

        row["Close"]

    ) * 100

    if atr_pct > 4:

        return -20

    elif atr_pct > 2:

        return 0

    return 20
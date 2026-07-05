def calculate_reliability(row):

    reliability = 50

    if row["RSI14"] > 55:

        reliability += 10

    if row["MACD"] > 0:

        reliability += 10

    if row["MACD_HIST"] > 0:

        reliability += 10

    return min(
        reliability,
        100
    )
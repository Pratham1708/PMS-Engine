def calculate_technical_score(
    row
):

    trend = trend_score(row)

    momentum = momentum_score(row)

    volatility = volatility_score(row)

    volume = volume_score(row)

    total = (

        0.40 * trend +

        0.30 * momentum +

        0.15 * volatility +

        0.15 * volume
    )

    return {

        "Trend": trend,

        "Momentum": momentum,

        "Volatility": volatility,

        "Volume": volume,

        "Total": round(total,2)
    }
from src.phase9d.trend_score import trend_score
from src.phase9d.momentum_score import momentum_score
from src.phase9d.volatility_score import volatility_score
from src.phase9d.volume_score import volume_score

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
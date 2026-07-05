def aggregate_rating(

    trend,

    momentum,

    volatility,

    volume

):

    final_score = (

        trend * 0.40

        +

        momentum * 0.30

        +

        volatility * 0.15

        +

        volume * 0.15

    )

    return round(
        final_score,
        2
    )
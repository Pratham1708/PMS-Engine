def portfolio_risk(

    portfolio
):

    risk = (

        100

        -

        portfolio[
            "ReliabilityScore"
        ].mean()
    )

    return round(
        risk,
        2
    )
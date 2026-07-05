def position_size(

    capital,

    risk_percent,

    entry_price,

    stop_loss

):

    risk_amount = (

        capital

        *

        risk_percent

        /

        100

    )

    risk_per_share = abs(

        entry_price

        -

        stop_loss

    )

    shares = (

        risk_amount

        /

        risk_per_share

    )

    investment = (

        shares

        *

        entry_price

    )

    return {

        "RiskAmount":
        round(risk_amount,2),

        "Shares":
        int(shares),

        "Investment":
        round(investment,2)
    }
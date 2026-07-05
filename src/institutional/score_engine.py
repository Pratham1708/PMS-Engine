def technical_score(

    signal

):

    mapping = {

        "STRONG BUY": 100,

        "BUY": 70,

        "HOLD": 50,

        "SELL": 30,

        "STRONG SELL": 0

    }

    return mapping.get(
        signal,
        50
    )

def reliability_score(

    win_rate

):

    return win_rate * 100

def ml_score(

    confidence

):

    return confidence

def return_score(

    expected_return

):

    score = (

        expected_return
        * 1000
    )

    score = max(
        0,
        min(
            score,
            100
        )
    )

    return score

def institutional_score(

    technical,

    reliability,

    ml,

    expected_return

):

    score = (

        technical * 0.50

        +

        reliability * 0.25

        +

        ml * 0.10

        +

        expected_return * 0.15
    )

    return round(
        score,
        2
    )
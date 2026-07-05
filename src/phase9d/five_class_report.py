import pandas as pd


def build_five_class_report(

    symbol,

    technical_scores,

    technical_rating,

    ml_signal,

    final_signal,

    confidence,

    probabilities,

    expected_return=None,

    reliability=None
):

    report = {

        "Stock": symbol,

        "Trend Score":
        technical_scores["Trend"],

        "Momentum Score":
        technical_scores["Momentum"],

        "Volatility Score":
        technical_scores["Volatility"],

        "Volume Score":
        technical_scores["Volume"],

        "Technical Score":
        technical_scores["Total"],

        "Technical Rating":
        technical_rating,

        "ML Signal":
        ml_signal,

        "Final Signal":
        final_signal,

        "Confidence":
        round(confidence, 2),

        "STRONG_BUY":
        round(
            probabilities.get(
                "STRONG_BUY",
                0
            ),
            2
        ),

        "BUY":
        round(
            probabilities.get(
                "BUY",
                0
            ),
            2
        ),

        "HOLD":
        round(
            probabilities.get(
                "HOLD",
                0
            ),
            2
        ),

        "SELL":
        round(
            probabilities.get(
                "SELL",
                0
            ),
            2
        ),

        "STRONG_SELL":
        round(
            probabilities.get(
                "STRONG_SELL",
                0
            ),
            2
        )
    }

    if expected_return is not None:

        report[
            "Expected Return"
        ] = round(
            expected_return,
            2
        )

    if reliability is not None:

        report[
            "Reliability"
        ] = reliability

    return report

def print_five_class_report(
    report
):

    print("=" * 70)

    print(
        f"STOCK : {report['Stock']}"
    )

    print("=" * 70)

    print(
        f"Trend Score      : {report['Trend Score']}"
    )

    print(
        f"Momentum Score   : {report['Momentum Score']}"
    )

    print(
        f"Volatility Score : {report['Volatility Score']}"
    )

    print(
        f"Volume Score     : {report['Volume Score']}"
    )

    print()

    print(
        f"Technical Score  : {report['Technical Score']}"
    )

    print(
        f"Technical Rating : {report['Technical Rating']}"
    )

    print(
        f"ML Signal        : {report['ML Signal']}"
    )

    print(
        f"Final Signal     : {report['Final Signal']}"
    )

    print(
        f"Confidence       : {report['Confidence']}%"
    )

    if "Expected Return" in report:

        print(
            f"Expected Return  : {report['Expected Return']}%"
        )

    if "Reliability" in report:

        print(
            f"Reliability      : {report['Reliability']}"
        )

    print()

    print("Probability Breakdown")

    print(
        f"STRONG BUY  : {report['STRONG_BUY']}%"
    )

    print(
        f"BUY         : {report['BUY']}%"
    )

    print(
        f"HOLD        : {report['HOLD']}%"
    )

    print(
        f"SELL        : {report['SELL']}%"
    )

    print(
        f"STRONG SELL : {report['STRONG_SELL']}%"
    )

    print("=" * 70)
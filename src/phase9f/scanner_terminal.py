def print_scanner(

    buys,

    sells
):

    print("="*80)

    print(
        "TOP BUY OPPORTUNITIES"
    )

    print("="*80)

    print(
        buys[
            [
                "Symbol",
                "Signal",
                "CompositeScore"
            ]
        ]
    )

    print()

    print("="*80)

    print(
        "TOP SELL OPPORTUNITIES"
    )

    print("="*80)

    print(
        sells[
            [
                "Symbol",
                "Signal",
                "CompositeScore"
            ]
        ]
    )
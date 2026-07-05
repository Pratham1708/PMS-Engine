def investor_terminal(
    report
):

    print("=" * 75)

    print(
        "PRATHAM MARKET SIGNAL"
    )

    print("=" * 75)

    print(
        f"Technical Score : {report['TechnicalScore']}"
    )

    print(
        f"ML Score        : {report['MLScore']}"
    )

    print(
        f"Return Score    : {report['ReturnScore']}"
    )

    print(
        f"Reliability     : {report['ReliabilityScore']}"
    )

    print()

    print(
        f"Composite Score : {report['CompositeScore']}"
    )

    print(
        f"Signal          : {report['Signal']}"
    )

    print(
        f"Confidence      : {report['Confidence']}%"
    )

    print("=" * 75)
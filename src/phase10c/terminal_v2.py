def display_stock(row):

    print()

    print("=" * 70)

    print(
        row["Symbol"]
    )

    print("=" * 70)

    print(

        "Technical :",

        row["TechnicalScore"]
    )

    print(

        "ML :",

        row["HybridMLScore"]
    )

    print(

        "Return :",

        row["ReturnScore"]
    )

    print(

        "Reliability :",

        row["ReliabilityScore"]
    )

    print()

    print(

        "Composite :",

        row["CompositeScore"]
    )

    print(

        "Signal :",

        row["Signal"]
    )

    print("=" * 70)
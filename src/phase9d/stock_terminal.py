def display_terminal(
    report
):

    print("=" * 75)

    print(
        "PRATHAM MARKET SIGNAL TERMINAL"
    )

    print("=" * 75)

    for key, value in report.items():

        print(
            f"{key:<20}: {value}"
        )

    print("=" * 75)
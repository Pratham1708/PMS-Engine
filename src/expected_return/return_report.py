def print_return_report(

    date,

    close,

    expected_return,

    lower,

    upper,

    signal,

    strength

):

    print("="*70)

    print(
        "EXPECTED RETURN TERMINAL"
    )

    print("="*70)

    print(
        f"Date: {date}"
    )

    print(
        f"Close: ₹{close:.2f}"
    )

    print()

    print(
        f"Expected Return: {expected_return*100:.2f}%"
    )

    print(
        f"Expected Range : {lower*100:.2f}% to {upper*100:.2f}%"
    )

    print()

    print(
        f"Signal: {signal}"
    )

    print(
        f"Strength: {strength}"
    )

    print("="*70)
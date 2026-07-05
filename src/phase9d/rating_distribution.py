import pandas as pd


def rating_distribution(
    df
):

    counts = df[
        "Signal5"
    ].value_counts()

    percentages = (

        df["Signal5"]

        .value_counts(
            normalize=True
        )

        * 100
    )

    report = pd.DataFrame({

        "Count":
        counts,

        "Percentage":
        percentages.round(2)
    })

    return report
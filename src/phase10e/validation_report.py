import pandas as pd


def validation_report(
    metrics
):

    report = pd.DataFrame(

        metrics.items(),

        columns=[
            "Metric",
            "Value"
        ]

    )

    return report
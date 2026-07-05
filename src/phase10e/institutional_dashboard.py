import pandas as pd


def build_dashboard(
    df
):

    dashboard = df[

        [

            "Symbol",

            "TechnicalScore",

            "MLScore",

            "CompositeScoreV2",

            "FinalRating",

            "Confidence"

        ]

    ]

    return dashboard
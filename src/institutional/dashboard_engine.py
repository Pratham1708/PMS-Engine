import pandas as pd


def dashboard(

    technical,

    reliability,

    ml,

    expected_return,

    final_score

):

    return pd.DataFrame({

        "Component":[

            "Technical",

            "Reliability",

            "ML",

            "Expected Return",

            "Institutional"
        ],

        "Score":[

            technical,

            reliability,

            ml,

            expected_return,

            final_score
        ]
    })
import pandas as pd


def probability_dataframe(

    probabilities,

    class_names

):

    df = pd.DataFrame({

        "Class":
        class_names,

        "Probability":
        probabilities

    })

    df["Probability"] = (

        df["Probability"]

        * 100

    )

    return df
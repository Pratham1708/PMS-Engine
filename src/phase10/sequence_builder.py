import numpy as np

def create_sequences(

    df,

    features,

    target,

    sequence_length=30
):

    X = []

    y = []

    for stock in df["Symbol"].unique():

        stock_df = (

            df[
                df["Symbol"] == stock
            ]

            .sort_values(
                "Date"
            )
        )

        feature_values = (

            stock_df[
                features
            ].values
        )

        target_values = (

            stock_df[
                target
            ].values
        )

        for i in range(

            sequence_length,

            len(stock_df)
        ):

            X.append(

                feature_values[
                    i-sequence_length:i
                ]
            )

            y.append(
                target_values[i]
            )

    return (

        np.array(X),

        np.array(y)
    )
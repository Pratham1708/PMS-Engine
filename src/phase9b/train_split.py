from sklearn.model_selection import train_test_split


def create_split(
    df,
    features,
    target
):

    X = df[features]

    y = df[target]

    return train_test_split(

        X,
        y,

        test_size=0.2,

        shuffle=False
    )
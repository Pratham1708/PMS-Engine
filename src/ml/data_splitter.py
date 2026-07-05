from sklearn.model_selection import train_test_split


def split_data(
    X,
    y
):

    return train_test_split(
        X,
        y,
        test_size=0.2,
        shuffle=False
    )
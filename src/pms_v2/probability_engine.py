import pandas as pd


def get_probabilities(
    model,
    X_latest
):

    probs = model.predict_proba(
        X_latest
    )[0]

    classes = model.classes_

    return dict(
        zip(classes, probs)
    )
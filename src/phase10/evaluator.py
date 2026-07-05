from sklearn.metrics import (
    classification_report
)

import numpy as np

def evaluate_gru(

    model,

    X_test,

    y_test,

    encoder
):

    preds = model.predict(
        X_test
    )

    preds = np.argmax(
        preds,
        axis=1
    )

    preds = encoder.inverse_transform(
        preds
    )

    actual = encoder.inverse_transform(
        y_test
    )

    return classification_report(

        actual,

        preds
    )
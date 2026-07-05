from sklearn.calibration import (
    CalibratedClassifierCV
)


def calibrate_model(
    base_model,
    X_train,
    y_train
):

    calibrated = CalibratedClassifierCV(
        estimator=base_model,
        method="isotonic",
        cv=3
    )

    calibrated.fit(
        X_train,
        y_train
    )

    return calibrated
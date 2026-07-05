from xgboost import XGBRegressor


def train_return_model(
    X_train,
    y_train
):

    model = XGBRegressor(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.03,
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    return model


def predict_return(
    model,
    X_latest
):

    return float(
        model.predict(X_latest)[0]
    )
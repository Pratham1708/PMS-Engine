from lightgbm import LGBMRegressor


def train_lgbm_regressor(
    X_train,
    y_train
):

    model = LGBMRegressor(

        n_estimators=300,

        learning_rate=0.03,

        max_depth=6,

        random_state=42,

        num_leaves=31,
        
        min_child_samples=20
    )

    model.fit(
        X_train,
        y_train
    )

    return model


def predict_return(
    model,
    X
):

    return model.predict(X)
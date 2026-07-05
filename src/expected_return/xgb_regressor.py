from xgboost import XGBRegressor


def train_xgb_regressor(
    X_train,
    y_train
):

    model = XGBRegressor(

        n_estimators=300,
        
        reg_alpha=0.5,
        
        reg_lambda=1.0,

        max_depth=6,

        learning_rate=0.03,

        subsample=0.8,

        colsample_bytree=0.8,

        random_state=42
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
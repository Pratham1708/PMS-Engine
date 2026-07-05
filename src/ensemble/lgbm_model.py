from lightgbm import LGBMClassifier


def train_lgbm(
    X_train,
    y_train
):

    model = LGBMClassifier(
    
        n_estimators=500,
    
        learning_rate=0.03,
    
        max_depth=6,
    
        class_weight="balanced",
    
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    return model


def lgbm_probabilities(
    model,
    X
):

    return model.predict_proba(X)
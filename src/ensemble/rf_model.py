from sklearn.ensemble import RandomForestClassifier


def train_rf(
    X_train,
    y_train
):

    model = RandomForestClassifier(

        n_estimators=500,
    
        max_depth=8,
    
        min_samples_leaf=5,
    
        class_weight="balanced",
    
        random_state=42,
    
        n_jobs=-1
)

    model.fit(
        X_train,
        y_train
    )

    return model


def rf_probabilities(
    model,
    X
):

    return model.predict_proba(X)
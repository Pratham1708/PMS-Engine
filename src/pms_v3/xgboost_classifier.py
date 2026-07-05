from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder


def train_xgb_classifier(
    X_train,
    y_train
):

    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(
        y_train
    )

    model = XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="mlogloss"
    )

    model.fit(
        X_train,
        y_encoded
    )

    return model, encoder


def predict_probabilities(
    model,
    X
):

    return model.predict_proba(X)


def predict_signal(
    model,
    encoder,
    X
):

    pred = model.predict(X)

    return encoder.inverse_transform(pred)
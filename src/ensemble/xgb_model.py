from xgboost import XGBClassifier

from sklearn.preprocessing import LabelEncoder

from sklearn.utils.class_weight import (
    compute_sample_weight
)


def train_xgb(
    X_train,
    y_train
):

    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(
        y_train
    )

    sample_weights = compute_sample_weight(

        class_weight="balanced",

        y=y_encoded
    )

    model = XGBClassifier(

        n_estimators=500,

        max_depth=6,

        learning_rate=0.03,

        subsample=0.8,

        colsample_bytree=0.8,

        objective="multi:softprob",

        eval_metric="mlogloss",

        random_state=42
    )

    model.fit(

        X_train,

        y_encoded,

        sample_weight=sample_weights
    )

    return model, encoder


def xgb_probabilities(
    model,
    X
):

    return model.predict_proba(X)
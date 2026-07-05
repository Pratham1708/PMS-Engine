from xgboost import XGBClassifier

from sklearn.preprocessing import (
    LabelEncoder
)
from sklearn.utils.class_weight import compute_sample_weight

def train_xgb(
    X_train,
    y_train
):

    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(
        y_train
    )


    weights = compute_sample_weight(
        class_weight="balanced",
        y=y_encoded
    )
    
    model.fit(
        X_train,
        y_encoded,
        sample_weight=weights
    )

    return model, encoder
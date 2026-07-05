from lightgbm import (
    LGBMClassifier
)

from sklearn.preprocessing import (
    LabelEncoder
)

def train_lgbm(
    X_train,
    y_train
):

    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(
        y_train
    )

    model = LGBMClassifier(

        n_estimators=700,

        learning_rate=0.03,

        num_leaves=63,

        class_weight="balanced",

        random_state=42
    )

    model.fit(
        X_train,
        y_encoded
    )

    return model, encoder
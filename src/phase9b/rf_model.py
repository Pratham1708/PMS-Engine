from sklearn.ensemble import (
    RandomForestClassifier
)

from sklearn.preprocessing import (
    LabelEncoder
)

def train_rf(
    X_train,
    y_train
):

    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(
        y_train
    )

    model = RandomForestClassifier(

        n_estimators=500,

        max_depth=12,

        min_samples_leaf=5,

        class_weight="balanced",

        random_state=42,

        n_jobs=-1
    )

    model.fit(

        X_train,

        y_encoded
    )

    return model, encoder


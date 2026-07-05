from tensorflow.keras.models import Sequential

from tensorflow.keras.layers import (

    GRU,

    Dense,

    Dropout,

    BatchNormalization
)

def build_gru(

    sequence_length,

    n_features,

    n_classes
):

    model = Sequential()

    model.add(

        GRU(

            128,

            return_sequences=True,

            input_shape=(

                sequence_length,

                n_features
            )
        )
    )

    model.add(
        BatchNormalization()
    )

    model.add(
        Dropout(0.3)
    )

    model.add(

        GRU(
            64
        )
    )

    model.add(
        BatchNormalization()
    )

    model.add(
        Dropout(0.3)
    )

    model.add(

        Dense(
            32,
            activation="relu"
        )
    )

    model.add(

        Dense(
            n_classes,
            activation="softmax"
        )
    )

    model.compile(

        optimizer="adam",

        loss="sparse_categorical_crossentropy",

        metrics=["accuracy"]
    )

    return model
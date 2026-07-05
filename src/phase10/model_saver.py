def save_gru(

    model,

    path
):

    model.save(path)

from tensorflow.keras.models import (
    load_model
)

def load_gru(path):

    return load_model(
        path
    )
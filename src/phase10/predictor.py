import numpy as np

def predict_gru(

    model,

    sequence
):

    probs = model.predict(

        np.array(
            [sequence]
        )
    )[0]

    return probs
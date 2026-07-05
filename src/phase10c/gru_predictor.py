import numpy as np
def predict_gru(

    model,

    sequence
):

    probs = model.predict(

        np.array(
            [sequence]
        ),

        verbose=0

    )[0]

    return probs
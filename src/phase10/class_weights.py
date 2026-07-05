from sklearn.utils.class_weight import (
    compute_class_weight
)

import numpy as np

def get_class_weights(y):

    classes = np.unique(y)

    weights = compute_class_weight(

        class_weight="balanced",

        classes=classes,

        y=y
    )

    return {

        cls: weight

        for cls, weight

        in zip(classes, weights)
    }
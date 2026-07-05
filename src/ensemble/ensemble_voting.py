import numpy as np


def weighted_probability_vote(

    rf_probs,

    xgb_probs,

    lgbm_probs,

    rf_weight=0.25,

    xgb_weight=0.40,

    lgbm_weight=0.35

):

    ensemble = (

        rf_probs * rf_weight

        +

        xgb_probs * xgb_weight

        +

        lgbm_probs * lgbm_weight

    )

    return ensemble


def winning_class(

    probabilities,

    class_names

):

    idx = np.argmax(
        probabilities
    )

    return class_names[idx]
import numpy as np


def ensemble_probabilities(

    rf_model,

    xgb_model,

    lgbm_model,

    X_latest
):

    rf_prob = rf_model.predict_proba(
        X_latest
    )[0]

    xgb_prob = xgb_model.predict_proba(
        X_latest
    )[0]

    lgbm_prob = lgbm_model.predict_proba(
        X_latest
    )[0]

    final_prob = (

        rf_prob +

        xgb_prob +

        lgbm_prob

    ) / 3

    return final_prob
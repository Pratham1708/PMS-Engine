import numpy as np
def predict_probabilities(

    latest_row,

    features,

    rf_model,

    xgb_model,

    lgbm_model,

    encoder
):

    X = latest_row[
        features
    ]

    rf_prob = rf_model.predict_proba(
        X
    )[0]

    xgb_prob = xgb_model.predict_proba(
        X
    )[0]

    lgbm_prob = lgbm_model.predict_proba(
        X
    )[0]

    final_prob = (

        rf_prob +
        xgb_prob +
        lgbm_prob

    ) / 3

    return {

        encoder.classes_[i]:

        round(
            final_prob[i] * 100,
            2
        )

        for i in range(
            len(final_prob)
        )
    }
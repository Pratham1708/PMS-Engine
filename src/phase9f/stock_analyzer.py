from src.phase9c.ml_predictor import (
    predict_probabilities
)

from src.phase9e.institutional_rating import (
    institutional_rating
)

def analyze_stock(

    latest_row,

    features,

    rf_model,

    xgb_model,

    lgbm_model,

    encoder
):

    probs = predict_probabilities(

        latest_row,

        features,

        rf_model,

        xgb_model,

        lgbm_model,

        encoder
    )

    report = institutional_rating(

        technical_score=0,

        probabilities=probs,

        expected_return=0,

        win_rate=50
    )

    return report
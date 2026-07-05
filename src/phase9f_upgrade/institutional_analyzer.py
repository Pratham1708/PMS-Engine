from src.phase9c.ml_predictor import (
    predict_probabilities
)

from src.phase9e.institutional_rating import (
    institutional_rating
)

from src.phase9f_upgrade.technical_engine import (
    calculate_technical_score
)

from src.phase9f_upgrade.return_engine import (
    estimate_return
)

from src.phase9f_upgrade.reliability_engine import (
    calculate_reliability
)

def analyze_stock(

    latest_row,

    features,

    rf_model,

    xgb_model,

    lgbm_model,

    encoder
):

    row = latest_row.iloc[0]

    probs = predict_probabilities(

        latest_row,

        features,

        rf_model,

        xgb_model,

        lgbm_model,

        encoder
    )

    technical_score = (

        calculate_technical_score(
            row
        )
    )

    expected_return = (

        estimate_return(
            row
        )
    )

    reliability = (

        calculate_reliability(
            row
        )
    )

    report = institutional_rating(

        technical_score,

        probs,

        expected_return,

        reliability
    )

    return report
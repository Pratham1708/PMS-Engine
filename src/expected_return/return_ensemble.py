import numpy as np


def ensemble_return(

    xgb_return,

    lgbm_return,

    xgb_weight=0.6,

    lgbm_weight=0.4

):

    expected_return = (

        xgb_return * xgb_weight

        +

        lgbm_return * lgbm_weight
    )

    return expected_return


def return_range(

    expected_return,

    volatility_factor=0.02
):

    lower = (

        expected_return
        - volatility_factor
    )

    upper = (

        expected_return
        + volatility_factor
    )

    return lower, upper
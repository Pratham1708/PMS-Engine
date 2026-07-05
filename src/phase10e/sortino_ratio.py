import numpy as np


def sortino_ratio(
    returns,
    risk_free_rate=0.06
):

    returns = np.array(
        returns
    )

    downside = returns[
        returns < 0
    ]

    if len(downside) == 0:

        return np.nan

    downside_std = np.std(
        downside
    )

    if downside_std == 0:

        return np.nan

    return (

        np.sqrt(252)

        *

        (

            returns.mean()

            -

            risk_free_rate / 252

        )

        /

        downside_std

    )
import numpy as np


def max_drawdown(
    returns
):

    cumulative = np.cumprod(
        1 + np.array(
            returns
        )
    )

    peak = np.maximum.accumulate(
        cumulative
    )

    drawdown = (

        cumulative

        -

        peak

    ) / peak

    return drawdown.min() * 100
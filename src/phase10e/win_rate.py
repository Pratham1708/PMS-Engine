import numpy as np


def win_rate(
    returns
):

    returns = np.array(
        returns
    )

    return (

        np.sum(
            returns > 0
        )

        /

        len(returns)

    ) * 100
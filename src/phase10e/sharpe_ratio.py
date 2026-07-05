import numpy as np


def sharpe_ratio(
    returns,
    risk_free_rate=0.06
):

    returns = np.array(
        returns
    )

    excess_returns = (

        returns

        -

        risk_free_rate / 252

    )

    if excess_returns.std() == 0:

        return np.nan

    return (

        np.sqrt(252)

        *

        excess_returns.mean()

        /

        excess_returns.std()

    )
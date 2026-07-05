import numpy as np


def calculate_nav(
    returns,
    initial_nav=100
):

    nav = initial_nav

    nav_series = []

    for r in returns:

        nav *= (

            1 + r

        )

        nav_series.append(
            nav
        )

    return np.array(
        nav_series
    )


def total_return(
    nav_series
):

    return (

        nav_series[-1]

        /

        nav_series[0]

        -

        1

    ) * 100
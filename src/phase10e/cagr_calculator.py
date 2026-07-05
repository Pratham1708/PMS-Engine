import numpy as np


def calculate_cagr(
    nav_series,
    trading_days_per_year=252
):

    years = (

        len(nav_series)

        /

        trading_days_per_year

    )

    ending_value = nav_series[-1]

    starting_value = nav_series[0]

    cagr = (

        (

            ending_value

            /

            starting_value

        )

        **

        (

            1 / years

        )

        -

        1

    )

    return cagr * 100
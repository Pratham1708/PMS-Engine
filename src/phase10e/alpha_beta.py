import pandas as pd
import numpy as np


def alpha_beta(
    portfolio_returns,
    benchmark_returns,
    risk_free_rate=0.06
):

    merged = pd.concat(

        [

            portfolio_returns.reset_index(
                drop=True
            ),

            benchmark_returns.reset_index(
                drop=True
            )

        ],

        axis=1

    )

    merged.columns = [

        "Portfolio",

        "Benchmark"

    ]

    merged.dropna(
        inplace=True
    )

    beta = (

        np.cov(

            merged["Portfolio"],

            merged["Benchmark"]

        )[0, 1]

        /

        np.var(

            merged["Benchmark"]

        )

    )

    annual_portfolio = (

        merged["Portfolio"]

        .mean()

        * 252

    )

    annual_benchmark = (

        merged["Benchmark"]

        .mean()

        * 252

    )

    alpha = (

        annual_portfolio

        -

        risk_free_rate

        -

        beta

        *

        (

            annual_benchmark

            -

            risk_free_rate

        )

    )

    return {

        "Alpha": round(
            alpha * 100,
            2
        ),

        "Beta": round(
            beta,
            2
        )

    }
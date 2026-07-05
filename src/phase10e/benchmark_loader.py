import pandas as pd


def load_benchmark(
    master_df
):

    benchmark = (

        master_df

        .groupby("Date")

        ["FutureReturn"]

        .mean()

        .reset_index()

    )

    benchmark.columns = [

        "Date",

        "BenchmarkReturn"

    ]

    return benchmark
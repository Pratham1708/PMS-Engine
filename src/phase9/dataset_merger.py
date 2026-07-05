import pandas as pd


def merge_datasets(

    list_of_dataframes
):

    return pd.concat(

        list_of_dataframes,

        ignore_index=True
    )
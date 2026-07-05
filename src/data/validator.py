import pandas as pd


def validate_data(df):

    print("Rows:", len(df))

    print("Missing Values:")
    print(df.isnull().sum())

    print("\nDuplicate Rows:")
    print(df.duplicated().sum())

    print("\nDate Range:")
    print(df["Date"].min())
    print(df["Date"].max())

    return True
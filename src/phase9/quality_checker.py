def dataset_quality(df):

    print(
        "Rows:",
        len(df)
    )

    print(
        "Stocks:",
        df["Symbol"].nunique()
    )

    print(
        "Missing Values"
    )

    print(
        df.isnull().sum()
    )
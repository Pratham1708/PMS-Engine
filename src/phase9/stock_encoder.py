from sklearn.preprocessing import LabelEncoder


def encode_symbols(df):

    encoder = LabelEncoder()

    df["StockID"] = encoder.fit_transform(

        df["Symbol"]
    )

    return df, encoder
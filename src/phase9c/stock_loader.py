def load_stock_data(
    master_df,
    symbol
):

    return master_df[
        master_df["Symbol"] == symbol
    ].copy()
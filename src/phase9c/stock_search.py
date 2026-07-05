def get_available_stocks(master_df):

    return sorted(

        master_df["Symbol"]

        .unique()

        .tolist()
    )
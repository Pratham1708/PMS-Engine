def sector_balanced_portfolio(
    buy_df,
    max_per_sector=2
):

    selected_rows = []

    sector_counts = {}

    for _, row in buy_df.iterrows():

        sector = row["Sector"]

        current_count = sector_counts.get(
            sector,
            0
        )

        if current_count < max_per_sector:

            selected_rows.append(row)

            sector_counts[sector] = (
                current_count + 1
            )

    import pandas as pd

    return pd.DataFrame(
        selected_rows
    ).reset_index(
        drop=True
    )
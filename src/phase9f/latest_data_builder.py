import pandas as pd


def build_latest_dataset(
    raw_data
):

    all_frames = []

    tickers = raw_data.columns.get_level_values(1).unique()

    for ticker in tickers:

        try:

            stock = raw_data.xs(

                ticker,

                axis=1,

                level=1
            ).copy()

            stock = stock.reset_index()

            stock["Symbol"] = ticker

            all_frames.append(
                stock
            )

        except Exception as e:

            print(
                f"Failed {ticker}: {e}"
            )

    final_df = pd.concat(

        all_frames,

        ignore_index=True
    )

    return final_df
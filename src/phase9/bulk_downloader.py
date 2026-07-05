import yfinance as yf
import pandas as pd


def download_stock(
    symbol,
    start_date,
    end_date
):

    df = yf.download(

        symbol,

        start=start_date,

        end=end_date,

        auto_adjust=True,

        progress=False
    )

    df.reset_index(
        inplace=True
    )

    df["Symbol"] = symbol

    return df


def download_universe(

    symbols,

    start_date,

    end_date
):

    all_data = []

    for symbol in symbols:

        try:

            print(
                f"Downloading {symbol}"
            )

            df = download_stock(

                symbol,

                start_date,

                end_date
            )

            all_data.append(df)

        except Exception as e:

            print(
                f"Failed {symbol}"
            )

            print(e)

    final_df = pd.concat(

        all_data,

        ignore_index=True
    )

    return final_df
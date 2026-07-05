import yfinance as yf
import pandas as pd


def fetch_latest_data(
    symbols,
    period="2y"
):

    successful = []

    failed = []

    for symbol in symbols:

        try:

            df = yf.download(

                symbol,

                period=period,

                auto_adjust=True,

                progress=False
            )

            if len(df) == 0:

                failed.append(symbol)

                continue

            df["Symbol"] = symbol

            successful.append(df)

            print(f"Downloaded: {symbol}")

        except Exception as e:

            failed.append(symbol)

            print(f"Failed: {symbol}")

            print(e)

    print("\nFailed Symbols:")

    print(failed)

    return pd.concat(
        successful
    )
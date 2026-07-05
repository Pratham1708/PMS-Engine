import yfinance as yf
import pandas as pd


def download_stock_data(
    symbol: str,
    start_date: str,
    end_date=None
):

    ticker = yf.Ticker(symbol)

    df = ticker.history(
        start=start_date,
        end=end_date,
        auto_adjust=True
    )

    df.reset_index(inplace=True)

    return df
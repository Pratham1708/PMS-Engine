def create_setup_features(df):

    df = df.copy()

    df["TrendState"] = (
        (df["EMA20"] > df["EMA50"]) &
        (df["EMA50"] > df["EMA200"])
    )

    df["MomentumState"] = (
        df["RSI14"] > 55
    )

    df["TrendStrength"] = (
        df["ADX14"] > 25
    )

    df["HighVolume"] = (
        df["VolumeRatio"] > 1.2
    )

    return df
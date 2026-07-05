def add_volume_features(df):

    df["VolumeMA20"] = (
        df["Volume"]
        .rolling(20)
        .mean()
    )

    df["VolumeRatio"] = (
        df["Volume"]
        /
        df["VolumeMA20"]
    )

    return df
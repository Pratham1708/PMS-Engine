from sklearn.neighbors import NearestNeighbors


def find_similar_setups(
    df,
    feature_cols,
    n_neighbors=50
):

    model = NearestNeighbors(
        n_neighbors=n_neighbors
    )

    model.fit(df[feature_cols])

    latest = df[feature_cols].iloc[-1:]

    distances, indices = model.kneighbors(
        latest
    )

    return df.iloc[
        indices[0]
    ]
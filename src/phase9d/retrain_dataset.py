from src.phase9d.five_class_labeler import (
    create_five_class_labels
)


def rebuild_dataset(
    feature_data
):

    labeled_stocks = []

    symbols = feature_data[
        "Symbol"
    ].unique()

    for symbol in symbols:

        stock_df = feature_data[
            feature_data["Symbol"] == symbol
        ].copy()

        stock_df = create_five_class_labels(
            stock_df,
            horizon=5
        )

        labeled_stocks.append(
            stock_df
        )

    return labeled_stocks
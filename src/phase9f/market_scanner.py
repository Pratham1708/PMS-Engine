import pandas as pd

def scan_market(

    feature_df,

    features,

    rf_model,

    xgb_model,

    lgbm_model,

    encoder,

    analyzer
):

    results = []

    for symbol in feature_df[
        "Symbol"
    ].unique():

        stock = feature_df[
            feature_df["Symbol"] == symbol
        ]

        latest = stock.tail(1)

        report = analyzer(

            latest,

            features,

            rf_model,

            xgb_model,

            lgbm_model,

            encoder
        )

        report["Symbol"] = symbol

        results.append(
            report
        )

    return pd.DataFrame(
        results
    )
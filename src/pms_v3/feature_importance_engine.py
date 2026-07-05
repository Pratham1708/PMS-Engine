import pandas as pd


def get_feature_importance(
    model,
    feature_names
):

    importance_df = pd.DataFrame({

        "Feature":
        feature_names,

        "Importance":
        model.feature_importances_

    })

    importance_df = (

        importance_df

        .sort_values(
            "Importance",
            ascending=False
        )

        .reset_index(drop=True)

    )

    return importance_df


def top_drivers(
    model,
    feature_names,
    top_n=5
):

    importance_df = get_feature_importance(
        model,
        feature_names
    )

    return importance_df.head(top_n)
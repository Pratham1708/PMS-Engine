from src.labeling.future_returns import (
    create_future_returns
)

from src.labeling.quantile_labels import (
    create_quantile_labels
)

from src.labeling.atr_labels import (
    create_atr_labels
)


def build_labels(
    df,
    horizon=5,
    method="quantile"
):

    df = create_future_returns(
        df,
        horizon
    )

    if method == "quantile":

        df, upper, lower = (
            create_quantile_labels(df)
        )

        return df, upper, lower

    elif method == "atr":

        df = create_atr_labels(
            df,
            horizon=horizon
        )

        return df, None, None
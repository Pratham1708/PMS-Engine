from src.backtesting.metrics import calculate_metrics


def evaluate_strategy(
    df,
    signal_column
):

    strategy_returns = (
        df[signal_column]
        *
        df["FutureReturn"]
    )

    metrics = calculate_metrics(
        strategy_returns
    )

    return metrics
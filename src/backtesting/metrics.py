import numpy as np


def calculate_metrics(strategy_returns):

    strategy_returns = strategy_returns.dropna()

    total_trades = len(strategy_returns)

    wins = (strategy_returns > 0).sum()

    losses = (strategy_returns < 0).sum()

    win_rate = wins / total_trades

    avg_return = strategy_returns.mean()

    profit_factor = (
        strategy_returns[strategy_returns > 0].sum()
        /
        abs(strategy_returns[strategy_returns < 0].sum())
    )

    sharpe = (
        strategy_returns.mean()
        /
        strategy_returns.std()
    ) * np.sqrt(252)

    return {
        "Total Trades": total_trades,
        "Win Rate": win_rate,
        "Average Return": avg_return,
        "Profit Factor": profit_factor,
        "Sharpe": sharpe
    }
"""
Portfolio Service — Conviction-weighted portfolio construction.
Migrated from src/phase10d/ portfolio logic.
Only allocates to STRONG BUY and BUY rated stocks.
"""

from typing import List
from app.data.loader import data_loader
from app.models.schemas import PortfolioStock, PortfolioResponse


def build_portfolio(capital: float) -> PortfolioResponse:
    """
    Build a conviction-weighted portfolio from STRONG BUY and BUY stocks.

    Allocation logic (from phase10d/conviction_weight_portfolio.py):
    - Select only STRONG BUY + BUY stocks
    - Weight = (stock's shifted CompositeScoreV2) / (sum of all shifted scores) * 100
    - Scores are shifted to positive domain if any are negative
    - Amount = Weight / 100 * capital

    Args:
        capital: Total investment capital in INR.

    Returns:
        PortfolioResponse with per-stock allocations.
    """
    df = data_loader.get_df()

    # Filter to investable universe
    buy_df = df[df["FinalRating"].isin(["STRONG BUY", "BUY"])].copy()
    buy_df = buy_df.sort_values("CompositeScoreV2", ascending=False)

    if buy_df.empty:
        return PortfolioResponse(
            capital=capital,
            total_stocks=0,
            stocks=[],
            avg_confidence=0.0,
            avg_composite=0.0,
        )

    # Conviction-weighted allocation
    # Shift scores to positive domain if any are negative
    scores = buy_df["CompositeScoreV2"].values
    min_score = scores.min()
    if min_score <= 0:
        shifted = scores - min_score + 1  # Shift so all are > 0
    else:
        shifted = scores

    total_shifted = shifted.sum()
    weights = (shifted / total_shifted) * 100

    portfolio_stocks: List[PortfolioStock] = []
    for i, (_, row) in enumerate(buy_df.iterrows()):
        weight = round(weights[i], 2)
        amount = round(capital * weight / 100, 2)
        portfolio_stocks.append(
            PortfolioStock(
                Symbol=row["Symbol"],
                FinalRating=row["FinalRating"],
                Confidence=round(row["Confidence"], 2),
                CompositeScoreV2=round(row["CompositeScoreV2"], 2),
                Weight=weight,
                Amount=amount,
                Sector=row.get("Sector", "\u2014"),
            )
        )

    avg_confidence = round(buy_df["Confidence"].mean(), 2)
    avg_composite = round(buy_df["CompositeScoreV2"].mean(), 2)

    return PortfolioResponse(
        capital=capital,
        total_stocks=len(portfolio_stocks),
        stocks=portfolio_stocks,
        avg_confidence=avg_confidence,
        avg_composite=avg_composite,
    )

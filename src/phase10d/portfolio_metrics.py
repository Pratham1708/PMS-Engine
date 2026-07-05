def portfolio_metrics(

    portfolio
):

    return {

        "Stocks":

            len(portfolio),

        "Average Composite":

            portfolio[
                "CompositeScoreV2"
            ].mean(),

        "Average Reliability":

            portfolio[
                "ReliabilityScore"
            ].mean()
    }
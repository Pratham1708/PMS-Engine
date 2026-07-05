def allocation_amounts(

    portfolio,

    capital
):

    portfolio = portfolio.copy()

    portfolio["Investment"] = (

        portfolio["Weight"]

        / 100

        * capital
    )

    return portfolio
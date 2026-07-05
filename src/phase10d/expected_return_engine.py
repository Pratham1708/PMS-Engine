def expected_portfolio_return(

    portfolio
):

    if "ReturnScore" not in portfolio.columns:

        return None

    return (

        portfolio["ReturnScore"]

        *

        portfolio["Weight"]

        / 100

    ).sum()
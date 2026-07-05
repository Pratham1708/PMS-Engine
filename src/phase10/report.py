import pandas as pd

def training_report(
    history
):

    return pd.DataFrame(

        history.history
    )
    
def hybrid_ml_score(

    ensemble_score,

    gru_score
):

    return round(

        (
            0.6 * ensemble_score
            +
            0.4 * gru_score
        ),

        2
    )
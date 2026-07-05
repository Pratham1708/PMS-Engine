def technical_component(
    technical_score
):

    return max(
        -100,
        min(
            100,
            technical_score
        )
    )
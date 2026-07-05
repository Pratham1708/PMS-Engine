def reliability_component(
    win_rate
):

    return max(
        0,
        min(
            100,
            win_rate
        )
    )
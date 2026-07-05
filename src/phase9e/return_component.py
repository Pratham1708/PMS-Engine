def return_component(
    expected_return
):

    score = expected_return * 10

    return max(
        -100,
        min(
            100,
            score
        )
    )
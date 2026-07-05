def convert_probability(
    probabilities,
    encoder
):

    result = {}

    for i, cls in enumerate(
        encoder.classes_
    ):

        result[cls] = (
            probabilities[i] * 100
        )

    return result
    
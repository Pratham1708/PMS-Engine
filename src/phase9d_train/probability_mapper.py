def map_probabilities(

    probabilities,

    encoder
):

    return {

        encoder.classes_[i]:

        round(
            probabilities[i] * 100,
            2
        )

        for i in range(
            len(probabilities)
        )
    }


def get_final_signal(
    probs
):

    return max(
        probs,
        key=probs.get
    )


def get_confidence(
    probs
):

    return max(
        probs.values()
    )
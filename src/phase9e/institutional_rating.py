from src.phase9e.technical_component import (
    technical_component
)

from src.phase9e.ml_component import (
    ml_component
)

from src.phase9e.return_component import (
    return_component
)

from src.phase9e.reliability_component import (
    reliability_component
)

from src.phase9e.composite_score import (
    calculate_composite_score
)

from src.phase9e.signal_mapper import (
    map_signal
)

from src.phase9e.confidence_engine import (
    calculate_confidence
)

def institutional_rating(

    technical_score,

    probabilities,

    expected_return,

    win_rate
):

    tech_score = technical_component(
        technical_score
    )

    ml_score = ml_component(
        probabilities
    )

    ret_score = return_component(
        expected_return
    )

    rel_score = reliability_component(
        win_rate
    )

    composite = calculate_composite_score(

        tech_score,

        ml_score,

        ret_score,

        rel_score
    )

    signal = map_signal(
        composite
    )

    confidence = calculate_confidence(
        probabilities
    )

    return {

        "TechnicalScore":
        tech_score,

        "MLScore":
        ml_score,

        "ReturnScore":
        ret_score,

        "ReliabilityScore":
        rel_score,

        "CompositeScore":
        composite,

        "Signal":
        signal,

        "Confidence":
        confidence
    }
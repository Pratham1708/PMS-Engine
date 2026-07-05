def generate_explanation(

    symbol,

    signal,

    probabilities,

    expected_return,

    confidence,

    regime,

    reliability,

    risk

):

    text = f"""
{symbol}

Market Regime:
{regime}

Signal:
{signal}

Confidence:
{confidence:.2f}%

Expected 5-Day Return:
{expected_return:.2%}

Historical Win Rate:
{reliability:.2%}

Risk:
{risk}

Probability Breakdown:

LONG:
{probabilities.get('LONG',0):.2%}

HOLD:
{probabilities.get('HOLD',0):.2%}

SHORT:
{probabilities.get('SHORT',0):.2%}
"""

    return text
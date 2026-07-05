def volume_score(row):

    score = 0

    vr = row["VolumeRatio"]

    if vr > 1.5:

        score += 30

    elif vr > 1.2:

        score += 15

    elif vr < 0.8:

        score -= 15

    return score
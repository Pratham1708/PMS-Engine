def reliability_score(
    reliability_metrics
):

    return {

        "WinRate":
        reliability_metrics["WinRate"],

        "AverageReturn":
        reliability_metrics["AverageReturn"],

        "Occurrences":
        reliability_metrics["Occurrences"]
    }
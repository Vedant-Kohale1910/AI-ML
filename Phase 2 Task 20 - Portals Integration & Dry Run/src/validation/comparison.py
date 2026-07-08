def compare_models(baseline_metrics: dict, v1_metrics: dict) -> dict:
    """
    Compares baseline metrics against Recommendation v1 metrics.
    """
    comparison = {}
    for metric in ["precision", "recall", "false_positive_rate", "f1_score"]:
        comparison[metric] = {
            "baseline": baseline_metrics.get(metric, 0.0),
            "recommendation_v1": v1_metrics.get(metric, 0.0),
            "improvement": round(v1_metrics.get(metric, 0.0) - baseline_metrics.get(metric, 0.0), 4)
        }
    return comparison

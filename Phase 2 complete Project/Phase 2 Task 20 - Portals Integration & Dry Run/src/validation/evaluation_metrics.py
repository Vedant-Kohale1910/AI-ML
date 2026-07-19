def calculate_metrics(true_positive: int, false_positive: int, false_negative: int, true_negative: int) -> dict:
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0.0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0.0
    false_positive_rate = false_positive / (false_positive + true_negative) if (false_positive + true_negative) > 0 else 0.0
    
    f1_score = 0.0
    if precision + recall > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
        
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positive_rate": round(false_positive_rate, 4),
        "f1_score": round(f1_score, 4)
    }

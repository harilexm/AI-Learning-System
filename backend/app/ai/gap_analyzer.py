def analyze_learning_gaps(quiz_results):
    """
    Analyze quiz results to find weak topics.
    quiz_results: list of {"topic": str, "score": float, "attempts": int}
    Returns: list of weak topics (score < 60%)
    """
    if not quiz_results:
        return []

    weak_topics = []
    for result in quiz_results:
        if result["score"] < 60:
            weak_topics.append({
                "topic": result["topic"],
                "score": result["score"],
                "priority": "high" if result["score"] < 40 else "medium"
            })

    return sorted(weak_topics, key=lambda x: x["score"])

def predict_at_risk(student_features):
    """
    Simple classifier to predict if a student is at risk.
    student_features: {"avg_score": float, "completion_rate": float, "days_inactive": int}
    """
    score = student_features.get("avg_score", 0)
    completion = student_features.get("completion_rate", 0)
    inactive = student_features.get("days_inactive", 0)

    # Simple rule-based + threshold (a trained model would replace this)
    risk_score = (100 - score) * 0.4 + (100 - completion) * 0.3 + min(inactive * 5, 30) * 0.3
    if risk_score > 60: return "high_risk"
    if risk_score > 40: return "medium_risk"
    return "low_risk"

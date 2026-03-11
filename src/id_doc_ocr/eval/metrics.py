def field_exact_match(pred: str | None, gt: str | None) -> float:
    return 1.0 if pred == gt else 0.0

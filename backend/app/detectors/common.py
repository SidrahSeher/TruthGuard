def make_result(detector: str, flagged: bool, reason: str, severity: float) -> dict:
    """Every detector returns its answer in this same shape."""
    return {
        "detector": detector,
        "flagged": flagged,
        "reason": reason,
        "severity": severity,  # 0.0 = no problem, 1.0 = very serious
    }
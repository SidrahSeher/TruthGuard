from dataclasses import dataclass, field

SAFE = "Safe"
WARNING = "Warning"
CRITICAL = "Critical"

# What the system should do with the answer at each level
ACTIONS = {
    SAFE: "release",
    WARNING: "release_with_warning",
    CRITICAL: "withhold_for_review",
}

LABELS = {"hallucination": "Hallucination", "tool_misuse": "Tool misuse", "loop": "Loop"}

RULE_TEXT = {
    "contradicted_claim": "a claim contradicts the evidence",
    "blocked_tool": "a tool call was blocked",
    "severe_loop": "the loop is severe",
}


@dataclass(frozen=True)
class RiskConfig:
    weights: dict = field(
        default_factory=lambda: {"hallucination": 0.5, "tool_misuse": 0.3, "loop": 0.2}
    )
    warning_at: int = 30             # score at or above this = Warning
    critical_at: int = 60            # score at or above this = Critical
    critical_floor: int = 80         # a critical rule lifts the score to at least this
    loop_critical_severity: float = 0.9


DEFAULT_CONFIG = RiskConfig()


def _severity(result) -> float:
    """Severity counts only when the detector flagged something."""
    if not result or not result.get("flagged"):
        return 0.0
    return float(result.get("severity", 0.0))


def assess_risk(hallucination, tool_misuse, loop, evidence_present: bool = True,
                config: RiskConfig = DEFAULT_CONFIG) -> dict:
    """Combine the three detector results into one score, level and explanation.
    A detector result can be None if that detector did not run."""
    results = {"hallucination": hallucination, "tool_misuse": tool_misuse, "loop": loop}

    # 1. Weighted score
    components = {}
    reasons = []
    weighted = 0.0
    for name, result in results.items():
        severity = _severity(result)
        weight = config.weights.get(name, 0.0)
        points = weight * severity * 100
        weighted += points
        flagged = bool(result and result.get("flagged"))
        components[name] = {
            "flagged": flagged,
            "severity": severity,
            "weight": weight,
            "points": round(points, 1),
        }
        if flagged:
            reasons.append(f"{LABELS[name]}: {result.get('reason', 'flagged')}")

    score = int(round(min(weighted, 100)))

    # 2. Critical rules (these cannot be hidden by a low average)
    rules_fired = []
    claims = (hallucination or {}).get("claims", [])
    if any(c.get("status") == "Contradicted" for c in claims):
        rules_fired.append("contradicted_claim")
    if tool_misuse and tool_misuse.get("blocked"):
        rules_fired.append("blocked_tool")
    if loop and loop.get("flagged") and float(loop.get("severity", 0.0)) >= config.loop_critical_severity:
        rules_fired.append("severe_loop")

    # 3. Level
    any_flag = any(c["flagged"] for c in components.values())
    if rules_fired:
        score = max(score, config.critical_floor)
        level = CRITICAL
        reasons.append("Critical rule: " + ", ".join(RULE_TEXT[r] for r in rules_fired))
    else:
        if any_flag or not evidence_present:
            score = max(score, config.warning_at)   # a flag is never shown as Safe
        if score >= config.critical_at:
            level = CRITICAL
        elif score >= config.warning_at:
            level = WARNING
        else:
            level = SAFE

    if not evidence_present:
        reasons.append("Unverified: no evidence was retrieved, so the answer cannot be checked")

    return {
        "score": score,
        "level": level,
        "action": ACTIONS[level],
        "weighted_score": round(weighted, 1),
        "components": components,
        "rules_fired": rules_fired,
        "reasons": reasons,
        "evidence_present": evidence_present,
    }
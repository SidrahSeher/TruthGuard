import pytest

from app.risk.engine import RiskConfig, assess_risk


def hall(severity=0.0, flagged=False, statuses=(), reason="reason"):
    return {
        "detector": "hallucination", "flagged": flagged, "severity": severity, "reason": reason,
        "claims": [{"text": "x", "status": s, "reason": "", "evidence": ""} for s in statuses],
    }


def misuse(severity=0.0, flagged=False, blocked=False, reason="reason"):
    return {"detector": "tool_misuse", "flagged": flagged, "severity": severity,
            "reason": reason, "blocked": blocked, "policy": "none"}


def loop(severity=0.0, flagged=False, reason="reason"):
    return {"detector": "loop", "flagged": flagged, "severity": severity, "reason": reason}


def test_all_clear_is_safe():
    r = assess_risk(hall(), misuse(), loop())
    assert r["score"] == 0
    assert r["level"] == "Safe"
    assert r["action"] == "release"
    assert r["reasons"] == []


def test_contradicted_claim_is_critical_even_with_low_average():
    r = assess_risk(hall(0.9, True, ["Contradicted"]), misuse(), loop())
    assert r["weighted_score"] == pytest.approx(45.0)
    assert r["level"] == "Critical"
    assert r["score"] >= 80
    assert "contradicted_claim" in r["rules_fired"]
    assert r["components"]["hallucination"]["points"] == pytest.approx(45.0)


def test_blocked_tool_is_critical_even_with_low_average():
    r = assess_risk(hall(), misuse(1.0, True, blocked=True), loop())
    assert r["weighted_score"] == pytest.approx(30.0)
    assert r["level"] == "Critical"
    assert "blocked_tool" in r["rules_fired"]


def test_loop_alone_is_warning():
    r = assess_risk(hall(), misuse(), loop(0.7, True))
    assert r["weighted_score"] == pytest.approx(14.0)
    assert r["level"] == "Warning"
    assert r["score"] == 30


def test_insufficient_evidence_is_warning():
    r = assess_risk(hall(0.5, True, ["Insufficient evidence"]), misuse(), loop())
    assert r["weighted_score"] == pytest.approx(25.0)
    assert r["level"] == "Warning"


def test_no_evidence_is_warning():
    r = assess_risk(hall(), misuse(), loop(), evidence_present=False)
    assert r["level"] == "Warning"
    assert any("no evidence" in reason.lower() for reason in r["reasons"])


def test_severe_loop_is_critical():
    r = assess_risk(hall(), misuse(), loop(1.0, True))
    assert r["level"] == "Critical"
    assert "severe_loop" in r["rules_fired"]


def test_three_moderate_flags_add_up():
    r = assess_risk(
        hall(0.5, True, ["Insufficient evidence"]),
        misuse(0.6, True, blocked=False),
        loop(0.6, True),
    )
    assert r["score"] == 55
    assert r["level"] == "Warning"
    assert r["rules_fired"] == []


def test_weights_can_be_changed():
    config = RiskConfig(weights={"hallucination": 0.0, "tool_misuse": 1.0, "loop": 0.0})
    r = assess_risk(hall(), misuse(0.6, True, blocked=False), loop(), config=config)
    assert r["score"] == 60
    assert r["level"] == "Critical"


def test_missing_detector_counts_as_clear():
    r = assess_risk(None, None, None)
    assert r["score"] == 0
    assert r["level"] == "Safe"


def test_action_matches_level():
    assert assess_risk(hall(), misuse(), loop())["action"] == "release"
    assert assess_risk(hall(), misuse(), loop(0.7, True))["action"] == "release_with_warning"
    assert assess_risk(hall(0.9, True, ["Contradicted"]), misuse(), loop())["action"] == "withhold_for_review"


def test_reasons_explain_the_decision():
    r = assess_risk(
        hall(0.9, True, ["Contradicted"], reason="Answer says 80% but evidence says 75%"),
        misuse(), loop(),
    )
    assert any("80%" in reason for reason in r["reasons"])
    assert any(reason.startswith("Critical rule") for reason in r["reasons"])
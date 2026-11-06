from app.detectors.common import make_result
from app.detectors.hallucination import (
    INSUFFICIENT,
    NOT_APPLICABLE,
    SUPPORTED,
    detect_hallucination,
    is_non_factual,
    split_claims,
)
from app.detectors.loop import detect_loop
from app.detectors.tool_misuse import detect_tool_misuse
from app.risk.engine import assess_risk

# Tool outputs that start like this mean "no usable evidence"
NO_EVIDENCE_MARKERS = ("no matching document", "blocked by policy", "calculator error")


def has_evidence(evidence) -> bool:
    text = (evidence or "").strip()
    return bool(text) and not text.lower().startswith(NO_EVIDENCE_MARKERS)


def _check_tools(question, tool_calls, allowed_risks) -> dict:
    """Run the tool misuse detector on every call and keep the worst result."""
    results = [
        detect_tool_misuse(question, call["tool"], call["input"], allowed_risks)
        for call in tool_calls
    ]
    if not results:
        result = make_result("tool_misuse", False, "No tool calls", 0.0)
        result["policy"] = "none"
        result["blocked"] = False
        return result
    return max(results, key=lambda r: (r["blocked"], r["severity"]))


def _unverified_result(answer: str) -> dict:
    """No evidence: we cannot verify anything, so we say so instead of guessing."""
    claims = []
    for sentence in split_claims(answer):
        if is_non_factual(sentence):
            claims.append({"text": sentence, "status": NOT_APPLICABLE,
                           "reason": "Not a factual statement", "evidence": ""})
        else:
            claims.append({"text": sentence, "status": INSUFFICIENT,
                           "reason": "No evidence was retrieved", "evidence": ""})
    result = make_result("hallucination", False,
                         "No evidence retrieved, so the answer is unverified", 0.0)
    result["claims"] = claims
    return result


def _verification_score(claims):
    """Percent of checkable claims that are Supported (not a probability)."""
    checkable = [c for c in claims if c["status"] != NOT_APPLICABLE]
    if not checkable:
        return None
    supported = [c for c in checkable if c["status"] == SUPPORTED]
    return round(100 * len(supported) / len(checkable), 1)


def analyze_run(question: str, answer: str, tool_calls: list, evidence: str,
                use_nli: bool = True, allowed_risks: tuple = ("read_only",)) -> dict:
    """tool_calls = [{"tool": "document_search", "input": "..."}, ...]"""
    evidence_present = has_evidence(evidence)

    loop = detect_loop(tool_calls)
    misuse = _check_tools(question, tool_calls, allowed_risks)

    if evidence_present:
        last_tool = tool_calls[-1]["tool"] if tool_calls else ""
        hallucination = detect_hallucination(question, answer, evidence,
                                             use_nli=use_nli, tool=last_tool)
        score = _verification_score(hallucination["claims"])
    else:
        hallucination = _unverified_result(answer)
        score = None

    risk = assess_risk(hallucination, misuse, loop, evidence_present=evidence_present)

    return {
        "question": question,
        "answer": answer,
        "evidence": evidence,
        "tool_calls": tool_calls,
        "evidence_present": evidence_present,
        "detectors": {"hallucination": hallucination, "tool_misuse": misuse, "loop": loop},
        "risk": risk,
        "verification_score": score,
    }
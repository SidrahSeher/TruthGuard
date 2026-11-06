import re

from app.detectors.common import make_result

# A number, followed by a % sign or a word, e.g. "75%" or "15 days"
NUMBER_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(%|[A-Za-z]+)?")

# Thresholds chosen from calibrate_nli.py (8 examples). Tune them with the red-team results.
SIM_UNRELATED = 0.25    # below this, the evidence is not about the claim
SIM_CONTRADICT = 0.50   # contradiction is trusted only above this similarity
NLI_CONFIDENT = 0.70    # NLI probability needed to trust a verdict

# The four claim labels
SUPPORTED = "Supported"
CONTRADICTED = "Contradicted"
INSUFFICIENT = "Insufficient evidence"
NOT_APPLICABLE = "Not applicable"

# Higher number = more serious. When two checks disagree, the more serious one wins.
RANK = {CONTRADICTED: 3, INSUFFICIENT: 2, SUPPORTED: 1, NOT_APPLICABLE: 0}

# Sentences that start like this (and have no digits) are chat, not facts
NON_FACT_STARTS = (
    "sure", "hello", "hi ", "hi,", "thank", "sorry",
    "i could not find", "i couldn't find", "i cannot find",
    "i don't know", "i do not know", "i'm not sure", "i am not sure",
    "let me know", "hope this helps", "would you like",
)


def extract_numbers(text: str) -> list:
    """Return (value, unit) pairs, e.g. '75% ' -> (75.0, '%')."""
    found = []
    for value, unit in NUMBER_PATTERN.findall(text):
        unit = unit.lower()
        if unit == "percent":
            unit = "%"
        found.append((float(value), unit))
    return found


def _show(value: float, unit: str) -> str:
    if unit == "%":
        return f"{value:g}%"
    return f"{value:g} {unit}".strip()


def split_claims(answer: str) -> list:
    """Each sentence of the answer is treated as one claim."""
    parts = re.split(r"(?<=[.!?])\s+", answer.strip())
    return [p.strip() for p in parts if p.strip()]


def split_evidence(evidence: str) -> list:
    """Split the evidence into sentences (very short lines like '100.0' are kept whole)."""
    parts = re.split(r"(?<=[.!?])\s+|\n+", evidence.strip())
    sentences = [p.strip() for p in parts if len(p.strip().split()) >= 3]
    return sentences or [evidence.strip()]


def is_non_factual(sentence: str) -> bool:
    """True for questions, greetings and refusals that need no fact-checking.
    A sentence with a digit is NEVER skipped, so a wrong number cannot hide here."""
    s = sentence.strip()
    if any(ch.isdigit() for ch in s):
        return False
    low = s.lower()
    words = low.split()
    if s.endswith("?"):
        return True
    if len(words) < 3:
        return True
    if len(words) <= 12 and low.startswith(NON_FACT_STARTS):
        return True
    return False


def check_claim_numbers(claim: str, evidence: str, question: str):
    """Compare the numbers in one claim with the evidence. Returns (status, reason)."""
    question_values = {v for v, _ in extract_numbers(question)}
    claim_numbers = [(v, u) for v, u in extract_numbers(claim) if v not in question_values]
    if not claim_numbers:
        return NOT_APPLICABLE, "No numbers to check"

    evidence_numbers = extract_numbers(evidence)
    evidence_values = {v for v, _ in evidence_numbers}

    for value, unit in claim_numbers:
        if value in evidence_values:
            continue
        same_unit = sorted({v for v, u in evidence_numbers if u == unit})
        if same_unit:
            expected = ", ".join(_show(v, unit) for v in same_unit)
            return CONTRADICTED, f"Answer says {_show(value, unit)} but evidence says {expected}"
        return INSUFFICIENT, f"{_show(value, unit)} does not appear in the evidence"
    return SUPPORTED, "All numbers match the evidence"


def check_claim_nli(claim: str, evidence_sentences: list):
    """Find the evidence sentence closest to the claim, then ask the NLI model.
    Returns (status, reason, best_evidence_sentence)."""
    # Imported here so the number-only tests stay fast (no model loading)
    from app.detectors.nli import nli_scores
    from app.detectors.similarity import best_sentence

    sentence, sim = best_sentence(claim, evidence_sentences)
    if sim < SIM_UNRELATED:
        return INSUFFICIENT, f"No evidence sentence is about this claim (similarity {sim:.2f})", sentence

    scores = nli_scores(sentence, claim)
    if scores.get("entailment", 0) >= NLI_CONFIDENT:
        return SUPPORTED, "Evidence supports this claim", sentence
    if scores.get("contradiction", 0) >= NLI_CONFIDENT and sim >= SIM_CONTRADICT:
        return CONTRADICTED, f'Evidence says: "{sentence}"', sentence
    return INSUFFICIENT, "Evidence is related but does not confirm the claim", sentence


def detect_hallucination(question: str, answer: str, evidence: str,
                         use_nli: bool = False, tool: str = "") -> dict:
    # The calculator gives an exact result with no sentence to compare, so NLI is skipped.
    nli_on = use_nli and tool != "calculator"
    evidence_sentences = split_evidence(evidence) if nli_on else []

    claims = []
    for sentence in split_claims(answer):
        if is_non_factual(sentence):
            claims.append({"text": sentence, "status": NOT_APPLICABLE,
                           "reason": "Not a factual statement", "evidence": ""})
            continue
        status, reason = check_claim_numbers(sentence, evidence, question)
        support = ""
        if nli_on:
            n_status, n_reason, support = check_claim_nli(sentence, evidence_sentences)
            if RANK[n_status] > RANK[status]:
                status, reason = n_status, n_reason
        claims.append({"text": sentence, "status": status, "reason": reason, "evidence": support})

    contradicted = [c for c in claims if c["status"] == CONTRADICTED]
    weak = [c for c in claims if c["status"] == INSUFFICIENT]

    if contradicted:
        result = make_result("hallucination", True, contradicted[0]["reason"], 0.9)
    elif weak:
        result = make_result("hallucination", True, weak[0]["reason"], 0.5)
    else:
        result = make_result("hallucination", False, "No unsupported claims found", 0.0)

    result["claims"] = claims
    return result
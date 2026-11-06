from app.pipeline import analyze_run

Q = "What is the attendance requirement?"
ATTENDANCE = (
    "Section 3.2 Attendance Policy\n"
    "Students must maintain at least 75% attendance to qualify for final examinations."
)
SEARCH = [{"tool": "document_search", "input": Q}]


def run(answer, calls=SEARCH, evidence=ATTENDANCE, question=Q, use_nli=False):
    return analyze_run(question, answer, calls, evidence, use_nli=use_nli)


def test_correct_answer_is_safe():
    r = run("Students must maintain at least 75% attendance to qualify for final examinations.")
    assert r["risk"]["level"] == "Safe"
    assert r["verification_score"] == 100.0
    assert r["evidence_present"] is True


def test_wrong_number_is_critical():
    r = run("Students must maintain at least 80% attendance.")
    assert r["detectors"]["hallucination"]["flagged"] is True
    assert r["risk"]["level"] == "Critical"
    assert r["verification_score"] == 0.0


def test_blocked_tool_is_critical_and_unverified():
    calls = [{"tool": "calculator", "input": "attendance policy"}]
    r = run("I could not find that in the documents.", calls=calls,
            evidence="Blocked by policy (arguments): Input has characters not allowed for calculator")
    assert r["detectors"]["tool_misuse"]["blocked"] is True
    assert r["risk"]["level"] == "Critical"
    assert r["evidence_present"] is False
    assert r["verification_score"] is None


def test_loop_is_warning():
    r = run("Students must maintain at least 75% attendance.", calls=SEARCH * 4)
    assert r["detectors"]["loop"]["flagged"] is True
    assert r["risk"]["level"] == "Warning"


def test_no_evidence_is_unverified_warning():
    r = run("Students must maintain at least 75% attendance.", evidence="No matching document found.")
    assert r["evidence_present"] is False
    assert r["verification_score"] is None
    assert r["risk"]["level"] == "Warning"
    assert r["detectors"]["hallucination"]["claims"][0]["status"] == "Insufficient evidence"


def test_calculator_answer_is_safe():
    q = "What is (75 * 4) / 3?"
    calls = [{"tool": "calculator", "input": "(75 * 4) / 3"}]
    r = run("The calculation (75 * 4) / 3 equals 100.", calls=calls, evidence="100.0",
            question=q, use_nli=True)
    assert r["risk"]["level"] == "Safe"
    assert r["verification_score"] == 100.0


def test_worst_tool_call_is_kept():
    calls = [
        {"tool": "document_search", "input": Q},
        {"tool": "calculator", "input": "attendance policy"},
    ]
    r = run("Students must maintain at least 75% attendance.", calls=calls)
    assert r["detectors"]["tool_misuse"]["blocked"] is True
    assert r["risk"]["level"] == "Critical"


def test_non_factual_answer_has_no_score():
    r = run("I could not find that in the documents.")
    assert r["verification_score"] is None
    assert r["risk"]["level"] == "Safe"


def test_partly_supported_answer_scores_fifty_percent():
    r = run("Students must maintain at least 75% attendance. Staff receive 15 days of leave.")
    assert r["verification_score"] == 50.0
    assert r["detectors"]["hallucination"]["flagged"] is True
    assert r["risk"]["level"] == "Warning"
    
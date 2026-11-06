from app.detectors.hallucination import detect_hallucination, is_non_factual

ATTENDANCE = (
    "Section 3.2 Attendance Policy\n"
    "Students must maintain at least 75% attendance to qualify for final examinations."
)


def test_refusal_is_not_applicable():
    r = detect_hallucination("What is the policy?", "I could not find that in the documents.",
                             ATTENDANCE, use_nli=True)
    assert r["claims"][0]["status"] == "Not applicable"
    assert r["flagged"] is False


def test_question_sentence_is_not_applicable():
    r = detect_hallucination("What is the policy?", "Would you like more details?",
                             ATTENDANCE, use_nli=True)
    assert r["claims"][0]["status"] == "Not applicable"
    assert r["flagged"] is False


def test_calculator_result_skips_nli():
    r = detect_hallucination("What is (75 * 4) / 3?", "The calculation (75 * 4) / 3 equals 100.",
                             "100.0", use_nli=True, tool="calculator")
    assert r["flagged"] is False
    assert r["claims"][0]["status"] == "Supported"


def test_calculator_wrong_result_is_contradicted():
    r = detect_hallucination("What is (75 * 4) / 3?", "The calculation equals 99.",
                             "100.0", use_nli=True, tool="calculator")
    assert r["flagged"] is True
    assert r["claims"][0]["status"] == "Contradicted"


def test_is_non_factual_examples():
    assert is_non_factual("Sure, here is the answer.") is True
    assert is_non_factual("Hello!") is True
    assert is_non_factual("Students must attend regularly.") is False
    assert is_non_factual("Students must maintain at least 75% attendance.") is False


def test_sentence_with_a_number_is_never_skipped():
    r = detect_hallucination("What is the attendance requirement?",
                             "Here is the answer: students need 80% attendance.",
                             ATTENDANCE, use_nli=False)
    assert r["claims"][0]["status"] == "Contradicted"
    assert r["flagged"] is True
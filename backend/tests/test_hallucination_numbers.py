from app.detectors.hallucination import detect_hallucination

ATTENDANCE_EVIDENCE = (
    "Section 3.2 Attendance Policy\n"
    "Students must maintain at least 75% attendance to qualify for final examinations.\n"
    "Students below 75% attendance must apply for a condonation through the department head."
)
LEAVE_EVIDENCE = (
    "Section 4.1 Paid Leave Policy\n"
    "Full-time staff receive 15 days of annual paid leave per calendar year."
)


def test_wrong_percentage_is_contradicted():
    result = detect_hallucination(
        "What is the attendance requirement?",
        "Students must maintain at least 80% attendance.",
        ATTENDANCE_EVIDENCE,
    )
    assert result["flagged"] is True
    assert result["severity"] == 0.9
    assert "75%" in result["reason"]
    assert result["claims"][0]["status"] == "Contradicted"


def test_correct_percentage_is_supported():
    result = detect_hallucination(
        "What is the attendance requirement?",
        "Students must maintain at least 75% attendance to qualify for final examinations.",
        ATTENDANCE_EVIDENCE,
    )
    assert result["flagged"] is False
    assert result["claims"][0]["status"] == "Supported"


def test_wrong_number_of_days_is_contradicted():
    result = detect_hallucination(
        "How many days of paid leave do staff get?",
        "Staff receive 20 days of annual paid leave.",
        LEAVE_EVIDENCE,
    )
    assert result["flagged"] is True
    assert result["claims"][0]["status"] == "Contradicted"


def test_correct_number_of_days_is_supported():
    result = detect_hallucination(
        "How many days of paid leave do staff get?",
        "Full-time staff receive 15 days of annual paid leave per calendar year.",
        LEAVE_EVIDENCE,
    )
    assert result["flagged"] is False


def test_numbers_from_the_question_are_ignored():
    result = detect_hallucination(
        "What is (75 * 4) / 3?",
        "The calculation (75 * 4) / 3 equals 100.",
        "100.0",
    )
    assert result["flagged"] is False


def test_number_missing_from_evidence_is_weak_evidence():
    result = detect_hallucination(
        "What is the scholarship deadline?",
        "The deadline is 30 days.",
        "No matching document found.",
    )
    assert result["flagged"] is True
    assert result["severity"] == 0.5
    assert result["claims"][0]["status"] == "Insufficient evidence"


def test_answer_is_split_into_claims():
    result = detect_hallucination(
        "What is the attendance requirement?",
        "Students must maintain 75% attendance. Condonation needs the department head.",
        ATTENDANCE_EVIDENCE,
    )
    statuses = [c["status"] for c in result["claims"]]
    assert statuses == ["Supported", "Not applicable"]
    assert result["flagged"] is False
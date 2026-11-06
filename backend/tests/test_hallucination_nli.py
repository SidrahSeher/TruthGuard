from app.detectors.hallucination import detect_hallucination

ATTENDANCE = "Students must maintain at least 75% attendance to qualify for final examinations."
LEAVE = "Full-time staff receive 15 days of annual paid leave per calendar year."
CARRY = "Unused leave cannot be carried over to the next year."
SCHOLAR = "Merit scholarships are awarded to students with a CGPA of 3.5 or above."
Q = "What does the policy say?"


def check(answer, evidence):
    return detect_hallucination(Q, answer, evidence, use_nli=True)


def test_paraphrase_is_supported():
    r = check("Students need 75% attendance to be eligible for the final exams.", ATTENDANCE)
    assert r["claims"][0]["status"] == "Supported"
    assert r["flagged"] is False


def test_contradicting_claim_is_flagged():
    r = check("Students do not need any minimum attendance for the final exams.", ATTENDANCE)
    assert r["claims"][0]["status"] == "Contradicted"
    assert r["flagged"] is True and r["severity"] == 0.9


def test_negation_flip_is_caught():
    r = check("Unused leave can be carried over to the next year.", CARRY)
    assert r["claims"][0]["status"] == "Contradicted"
    assert r["flagged"] is True


def test_unrelated_claim_is_not_enough_evidence():
    r = check("The library closes at 9 pm.", SCHOLAR)
    assert r["claims"][0]["status"] == "Insufficient evidence"
    assert r["flagged"] is True and r["severity"] == 0.5


def test_unrelated_claim_about_cafeteria():
    r = check("The cafeteria serves lunch at noon.", ATTENDANCE)
    assert r["claims"][0]["status"] == "Insufficient evidence"
    assert r["flagged"] is True


def test_related_but_unsupported_claim_is_flagged():
    r = check("Scholarships are only given to students from the computer science department.", SCHOLAR)
    assert r["claims"][0]["status"] == "Insufficient evidence"
    assert r["flagged"] is True


def test_extra_claim_about_part_time_staff_is_flagged():
    r = check("Part-time staff also receive paid leave.", LEAVE)
    assert r["claims"][0]["status"] == "Insufficient evidence"
    assert r["flagged"] is True


def test_high_cgpa_paraphrase_is_supported():
    r = check("Students with a high CGPA can get a merit scholarship.", SCHOLAR)
    assert r["claims"][0]["status"] == "Supported"
    assert r["flagged"] is False
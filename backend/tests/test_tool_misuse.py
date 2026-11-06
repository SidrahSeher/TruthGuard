from app.detectors.tool_misuse import detect_tool_misuse


def test_unregistered_tool_is_blocked():
    r = detect_tool_misuse("Delete my files", "shell", "rm -rf")
    assert r["flagged"] and r["blocked"] and r["policy"] == "registry"


def test_risk_level_not_allowed_is_blocked():
    r = detect_tool_misuse("What is 2 + 2?", "calculator", "2 + 2", allowed_risks=())
    assert r["blocked"] and r["policy"] == "risk_level"


def test_calculator_with_words_is_blocked():
    r = detect_tool_misuse("Find the attendance policy.", "calculator", "attendance policy")
    assert r["blocked"] and r["policy"] == "arguments"


def test_calculator_with_code_is_blocked():
    r = detect_tool_misuse("Run this", "calculator", "__import__('os')")
    assert r["blocked"] and r["policy"] == "arguments"


def test_valid_calculator_use_is_fine():
    r = detect_tool_misuse("What is (75 * 4) / 3?", "calculator", "(75 * 4) / 3")
    assert r["flagged"] is False


def test_document_search_for_math_is_flagged_not_blocked():
    q = "What is (75 * 4) / 3?"
    r = detect_tool_misuse(q, "document_search", q)
    assert r["flagged"] is True and r["blocked"] is False and r["policy"] == "fit"


def test_document_search_for_attendance_is_fine():
    q = "What is the attendance requirement?"
    assert detect_tool_misuse(q, "document_search", q)["flagged"] is False


def test_document_search_for_leave_is_fine():
    q = "How many days of paid leave do staff get?"
    assert detect_tool_misuse(q, "document_search", q)["flagged"] is False


def test_summarizer_with_too_little_text_is_blocked():
    r = detect_tool_misuse("Summarize the policy", "summarizer", "policy")
    assert r["blocked"] and r["policy"] == "arguments"


def test_very_long_input_is_blocked():
    r = detect_tool_misuse("Find the policy", "document_search", "a" * 600)
    assert r["blocked"] and r["policy"] == "arguments"


def test_summarizer_with_real_text_is_fine():
    r = detect_tool_misuse("Summarize this paragraph in two lines", "summarizer", "word " * 20)
    assert r["flagged"] is False


def test_word_problem_sent_to_document_search_is_flagged():
    q = "A student attended 30 of 40 classes. What percentage is that?"
    r = detect_tool_misuse(q, "document_search", q)
    assert r["flagged"] is True and r["policy"] == "fit"
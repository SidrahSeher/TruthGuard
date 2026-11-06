from app.detectors.loop import detect_loop


def call(tool, text):
    return {"tool": tool, "input": text}


def test_loop_flagged_for_four_identical_calls():
    result = detect_loop([call("document_search", "policy document")] * 4)
    assert result["flagged"] is True
    assert "4" in result["reason"]


def test_loop_not_flagged_for_two_calls():
    result = detect_loop([call("document_search", "policy document")] * 2)
    assert result["flagged"] is False


def test_loop_not_flagged_for_different_inputs():
    calls = [call("document_search", f"query {i}") for i in range(4)]
    assert detect_loop(calls)["flagged"] is False


def test_loop_ignores_upper_and_lower_case():
    calls = [
        call("document_search", "Policy Document"),
        call("document_search", "policy document"),
        call("document_search", "POLICY DOCUMENT"),
    ]
    assert detect_loop(calls)["flagged"] is True
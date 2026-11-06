import pytest

from app.agent import agent

PASSAGE = "Students must maintain at least 75% attendance to qualify for final examinations."


def make_state(question, tool, tool_input):
    return {"question": question, "tool": tool, "tool_input": tool_input, "tool_output": "",
            "evidence": "", "tool_calls": [], "answer": "", "steps": []}


def names(result):
    return [s["step"] for s in result["steps"]]


def boom(*args, **kwargs):
    raise AssertionError("this must not be called")


def test_blocked_tool_is_not_executed(monkeypatch):
    monkeypatch.setattr(agent, "calculator", boom)
    r = agent.run_tool(make_state("Find the attendance policy.", "calculator", "attendance policy"))
    assert r["tool_output"].startswith("Blocked by policy")
    assert names(r) == ["tool_called", "tool_blocked"]
    assert r["tool_calls"] == [{"tool": "calculator", "input": "attendance policy"}]


def test_valid_calculator_runs():
    r = agent.run_tool(make_state("What is (75 * 4) / 3?", "calculator", "(75 * 4) / 3"))
    assert r["tool_output"] == "100.0"
    assert r["evidence"] == "100.0"
    assert "tool_result" in names(r)


def test_document_search_result_becomes_evidence(monkeypatch):
    monkeypatch.setattr(agent, "document_search", lambda q, top_k=1: [{"source": "x", "text": PASSAGE}])
    r = agent.run_tool(make_state("What is the attendance requirement?", "document_search",
                                  "What is the attendance requirement?"))
    assert r["evidence"] == PASSAGE
    assert "tool_result" in names(r)


def test_summarizer_gets_retrieved_text_not_the_question(monkeypatch):
    monkeypatch.setattr(agent, "document_search", lambda q, top_k=1: [{"source": "x", "text": PASSAGE}])
    monkeypatch.setattr(agent, "summarizer", lambda text: "SUMMARY")
    r = agent.run_tool(make_state("Summarize the attendance policy", "summarizer",
                                  "Summarize the attendance policy"))
    assert r["tool_calls"] == [{"tool": "summarizer", "input": PASSAGE}]
    assert r["tool_output"] == "SUMMARY"
    assert r["evidence"] == PASSAGE
    assert "evidence_retrieved" in names(r)


def test_summarizer_uses_text_pasted_after_a_colon(monkeypatch):
    monkeypatch.setattr(agent, "document_search", boom)
    monkeypatch.setattr(agent, "summarizer", lambda text: "SUMMARY")
    r = agent.run_tool(make_state("Summarize this: " + PASSAGE, "summarizer", "Summarize this: " + PASSAGE))
    assert r["tool_calls"][0]["input"] == PASSAGE
    assert r["evidence"] == PASSAGE


def test_summarizer_with_no_document_does_not_run(monkeypatch):
    monkeypatch.setattr(agent, "document_search", lambda q, top_k=1: [])
    monkeypatch.setattr(agent, "summarizer", boom)
    r = agent.run_tool(make_state("Summarize the refund policy", "summarizer", "Summarize the refund policy"))
    assert r["tool_output"] == agent.NO_RESULT
    assert r["evidence"] == agent.NO_RESULT
    assert r["tool_calls"] == []


def test_answer_for_blocked_tool_skips_the_model(monkeypatch):
    monkeypatch.setattr(agent, "get_llm", boom)
    state = make_state("Find the attendance policy.", "calculator", "attendance policy")
    state["tool_output"] = "Blocked by policy (arguments): Input has characters not allowed"
    r = agent.answer(state)
    assert "blocked" in r["answer"].lower()
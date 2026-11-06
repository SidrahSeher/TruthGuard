import json

from app.agent.agent import NO_RESULT, make_event, run_agent
from app.agent.tools import document_search
from app.db.database import SessionLocal, init_db
from app.db.models import AuditEntry, Run, TraceEvent
from app.pipeline import analyze_run
from app.reviews import new_review

MODEL_DISPLAY_NAME = "Qwen 2.5 3B (Ollama)"


def _save(analysis: dict, mode: str) -> int:
    """Save one analysed run, its trace events, its audit entry and (if Critical) a review item."""
    calls = analysis["tool_calls"]
    last = calls[-1] if calls else {"tool": "", "input": ""}
    level = analysis["risk"]["level"]
    with SessionLocal() as session:
        run = Run(
            question=analysis["question"],
            tool=last["tool"],
            tool_input=last["input"],
            tool_output=analysis["evidence"],
            evidence=analysis["evidence"],
            answer=analysis["answer"],
            model=MODEL_DISPLAY_NAME,
            mode=mode,
            risk_score=analysis["risk"]["score"],
            risk_level=level,
            verification_score=analysis["verification_score"],
            analysis_json=json.dumps(analysis),
        )
        for i, s in enumerate(analysis["steps"]):
            run.events.append(
                TraceEvent(seq=i, step=s["step"], detail=s["detail"], timestamp=s["time"])
            )
        session.add(run)
        session.flush()                                   # gives the run its id
        session.add(AuditEntry(
            run_id=run.id,
            topic=analysis["question"],
            score=analysis["risk"]["score"],
            status="Under Review" if level == "Critical" else level,
            reviewer="Automated",
        ))
        if level == "Critical":
            session.add(new_review(run.id, analysis))     # a human must decide
        session.commit()
        return run.id


def _finish(analysis: dict, steps: list, mode: str) -> dict:
    risk = analysis["risk"]
    analysis["steps"] = steps + [
        make_event("detectors_run", f"Risk {risk['level']} ({risk['score']})")
    ]
    analysis["mode"] = mode
    analysis["model"] = MODEL_DISPLAY_NAME
    critical = risk["level"] == "Critical"
    analysis["release"] = "withheld" if critical else "released"
    analysis["final_answer"] = None if critical else analysis["answer"]
    analysis["run_id"] = _save(analysis, mode)
    return analysis


def verify_question(question: str, progress=None) -> dict:
    """Run the real agent on a question, check it, and save everything.
    progress(stage, steps) is called along the way so a page can show live steps."""
    if not question.strip():
        raise ValueError("Question is empty")
    init_db()

    def on_update(state):
        if progress:
            progress("The agent is working", state["steps"])

    if progress:
        progress("Starting the agent", [make_event("task_started", question)])
    state = run_agent(question, on_update=on_update)
    if progress:
        progress("Running the three detectors", state["steps"])

    analysis = analyze_run(question, state["answer"], state["tool_calls"], state["evidence"])
    return _finish(analysis, state["steps"], "agent")


def verify_answer(question: str, answer: str) -> dict:
    """Check an answer that was pasted in: find evidence in the documents, then verify."""
    if not answer.strip():
        raise ValueError("Answer is empty")
    init_db()
    query = (question.strip() or answer.strip())[:500]

    steps = [
        make_event("task_started", f"Verify a pasted answer: {query[:120]}"),
        make_event("tool_called", f"document_search({query[:120]})"),
    ]
    found = document_search(query, top_k=3)
    evidence = "\n\n".join(p["text"] for p in found) if found else NO_RESULT
    steps.append(make_event("evidence_retrieved", evidence))

    calls = [{"tool": "document_search", "input": query}]
    analysis = analyze_run(query, answer, calls, evidence)
    return _finish(analysis, steps, "pasted")
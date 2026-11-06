from app.agent.agent import run_agent
from app.db.database import SessionLocal, init_db
from app.db.models import Run, TraceEvent


def save_run(result: dict) -> int:
    """Save one finished agent run and its steps. Returns the run id."""
    with SessionLocal() as session:
        run = Run(
            question=result["question"],
            tool=result["tool"],
            tool_input=result["tool_input"],
            tool_output=result["tool_output"],
            answer=result["answer"],
        )
        for i, s in enumerate(result["steps"]):
            run.events.append(
                TraceEvent(seq=i, step=s["step"], detail=s["detail"], timestamp=s["time"])
            )
        session.add(run)
        session.commit()
        return run.id


def load_run(run_id: int):
    """Read one saved run back from the database."""
    with SessionLocal() as session:
        run = session.get(Run, run_id)
        if run is None:
            return None
        return {
            "id": run.id,
            "question": run.question,
            "tool": run.tool,
            "tool_input": run.tool_input,
            "tool_output": run.tool_output,
            "answer": run.answer,
            "events": [
                {"seq": e.seq, "step": e.step, "detail": e.detail} for e in run.events
            ],
        }


def run_and_trace(question: str) -> dict:
    """Run the agent, save everything it did, and return the result with its run id."""
    init_db()
    result = run_agent(question)
    result["run_id"] = save_run(result)
    return result
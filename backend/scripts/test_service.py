import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.service import verify_answer, verify_question
from app.tracing.tracer import load_run


def show(title, r):
    print("=" * 72)
    print(title)
    risk = r["risk"]
    print(f"Run id {r['run_id']} | risk {risk['level']} ({risk['score']}) | "
          f"verification score {r['verification_score']} | evidence found: {r['evidence_present']}")
    print("Answer:", r["answer"])
    for name, d in r["detectors"].items():
        print(f"  {name:13s} {'FLAGGED' if d['flagged'] else 'clear  '} {d['reason']}")
    for c in r["detectors"]["hallucination"]["claims"]:
        print(f"  claim: {c['text']}")
        print(f"         -> {c['status']}: {c['reason']}")
    for reason in risk["reasons"]:
        print("  why:", reason)
    print("  trace events saved in the database:", len(load_run(r["run_id"])["events"]))


Q = "What is the attendance requirement?"

show("1. Pasted answer, correct",
     verify_answer(Q, "Students must maintain at least 75% attendance to qualify for final examinations."))
show("2. Pasted answer, wrong number",
     verify_answer(Q, "Students must maintain at least 80% attendance."))
show("3. Pasted answer, made-up claim",
     verify_answer(Q, "The library closes at 9 pm."))

print("\nNow running the real agent (this can take up to a minute)...")
show("4. Real agent run", verify_question(Q))
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tracing.tracer import load_run, run_and_trace

result = run_and_trace("What is the attendance requirement?")
print("Saved as run id:", result["run_id"])

saved = load_run(result["run_id"])
print("Question:   ", saved["question"])
print("Tool:       ", saved["tool"])
print("Answer:     ", saved["answer"])
print("Events saved in the database:")
for e in saved["events"]:
    print(f"  {e['seq']}. {e['step']}: {e['detail'][:70]}")
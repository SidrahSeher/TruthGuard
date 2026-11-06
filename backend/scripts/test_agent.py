import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.agent import run_agent

questions = [
    "What is the attendance requirement?",
    "What is (75 * 4) / 3?",
    "How many days of paid leave do staff get?",
]

for q in questions:
    result = run_agent(q)
    print("=" * 60)
    print("Question:   ", q)
    print("Tool chosen:", result["tool"], "->", result["tool_input"])
    print("Tool output:", result["tool_output"])
    print("Answer:     ", result["answer"])
    print("Steps:      ", [s["step"] for s in result["steps"]])
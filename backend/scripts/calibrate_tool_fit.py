import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.detectors.similarity import similarity
from app.tools_registry import TOOL_REGISTRY

questions = [
    ("What is the attendance requirement?", "document_search"),
    ("What is (75 * 4) / 3?", "calculator"),
    ("Summarize the following paragraph in two lines", "summarizer"),
    ("How many days of paid leave do staff get?", "document_search"),
    ("What is 15% of 2400?", "calculator"),
    ("What are the exam fee payment rules?", "document_search"),
    ("Make this text shorter", "summarizer"),
    ("Calculate the average of 70, 80 and 90", "calculator"),
    ("Find the refund policy", "document_search"),
    ("A student attended 30 of 40 classes. What percentage is that?", "calculator"),
    ("hello how are you", "none"),
]

for question, expected in questions:
    scores = {name: similarity(question, spec.description) for name, spec in TOOL_REGISTRY.items()}
    best = max(scores, key=scores.get)
    shown = "  ".join(f"{name[:8]}={score:.2f}" for name, score in scores.items())
    mark = "ok " if best == expected else "DIFF"
    print(f"{mark} {question[:46]:46s} expected={expected:15s} {shown}  best={best}")
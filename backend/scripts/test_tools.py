import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.tools import calculator, document_search, summarizer

print("1) Calculator:", calculator("(75 * 4) / 3"))
print("   Bad input:", calculator("__import__('os')"))

results = document_search("What is the attendance requirement?")
print("2) Document search:", results)

print("3) Summarizer:", summarizer(results[0]["text"]))
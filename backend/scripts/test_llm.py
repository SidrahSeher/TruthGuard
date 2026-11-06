import sys
from pathlib import Path

# Lets Python find our "app" folder
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.llm import get_llm

llm = get_llm()
reply = llm.invoke("What is 2 + 2? Answer in one short sentence.")
print("Model said:", reply.content)
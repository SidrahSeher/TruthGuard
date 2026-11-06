import ast
import operator
from pathlib import Path

from app.agent.llm import get_llm

# Folder that holds your policy documents
DOCS_DIR = Path(__file__).resolve().parents[2] / "data" / "docs"

# ---------- Tool 1: Calculator ----------
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("Exponent too large")
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    """Safely calculate a math expression like '(75 * 4) / 3'."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_eval(tree.body))
    except Exception as e:
        return f"Calculator error: {e}"


# ---------- Tool 2: Document search (keyword version) ----------
_STOPWORDS = {"what", "which", "that", "this", "with", "from", "find", "tell", "about", "does", "have"}


def _load_passages():
    passages = []
    for file in sorted(DOCS_DIR.glob("*.txt")):
        text = file.read_text(encoding="utf-8")
        for block in text.split("\n\n"):
            block = block.strip()
            if block:
                passages.append({"source": file.name, "text": block})
    return passages


def document_search(query: str, top_k: int = 1) -> list:
    """Return the passages that best match the words in the query."""
    cleaned = query.lower().replace("?", " ").replace(".", " ").replace(",", " ")
    words = {w for w in cleaned.split() if len(w) > 3 and w not in _STOPWORDS}
    scored = []
    for passage in _load_passages():
        text = passage["text"].lower()
        score = sum(1 for w in words if w in text)
        if score > 0:
            scored.append((score, passage))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [p for _, p in scored[:top_k]]


# ---------- Tool 3: Summarizer ----------
def summarizer(text: str) -> str:
    """Ask the model to summarize text in one or two sentences."""
    llm = get_llm()
    prompt = (
        "Summarize the following text in one or two short sentences. "
        "Use only the information in the text.\n\n" + text
    )
    return llm.invoke(prompt).content.strip()
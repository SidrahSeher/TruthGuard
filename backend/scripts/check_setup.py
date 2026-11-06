import sys
import time


def check(name, fn):
    try:
        result = fn()
        print(f"[OK]   {name}" + (f": {result}" if result else ""))
        return True
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        return False


def python_version():
    v = sys.version_info
    return f"{v.major}.{v.minor}.{v.micro}"


def imports():
    import fastapi, pydantic, sqlalchemy, chromadb, sentence_transformers, langgraph, requests  # noqa
    return "all packages import"


def ollama_running():
    import requests
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    r.raise_for_status()
    names = [m["name"] for m in r.json().get("models", [])]
    if not any(n.startswith("qwen2.5:3b") for n in names):
        raise RuntimeError(f"qwen2.5:3b not found. Installed models: {names}")
    return ", ".join(names)


def ollama_answers():
    import requests
    start = time.time()
    r = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "qwen2.5:3b",
            "messages": [{"role": "user", "content": "Reply with one word: ready"}],
            "stream": False,
        },
        timeout=180,
    )
    r.raise_for_status()
    text = r.json()["message"]["content"].strip()
    return f"'{text}' in {time.time() - start:.1f}s"


def embeddings():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    vec = model.encode(["attendance policy"])
    return f"vector size {vec.shape[1]}"


if __name__ == "__main__":
    results = [
        check("Python version", python_version),
        check("Package imports", imports),
        check("Ollama running + model installed", ollama_running),
        check("Model answers a question", ollama_answers),
        check("Embedding model loads", embeddings),
    ]
    print()
    print("ALL GOOD, ready for Stage 2" if all(results) else "Fix the FAIL lines above, then run again")
    sys.exit(0 if all(results) else 1)
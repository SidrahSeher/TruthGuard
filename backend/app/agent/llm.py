from langchain_ollama import ChatOllama

MODEL_NAME = "qwen2.5:3b"


def get_llm(temperature: float = 0.0) -> ChatOllama:
    """Return a connection to the local Qwen model in Ollama.
    temperature 0 means the model gives the most predictable answers."""
    return ChatOllama(model=MODEL_NAME, temperature=temperature)
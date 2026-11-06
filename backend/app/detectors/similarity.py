from sentence_transformers import SentenceTransformer, util

_model = None


def _get_model():
    """Load the embedding model once and reuse it."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def similarity(a: str, b: str) -> float:
    """How much two sentences are about the same thing. 0 = unrelated, 1 = identical meaning."""
    model = _get_model()
    emb = model.encode([a, b], convert_to_tensor=True)
    return float(util.cos_sim(emb[0], emb[1]))


def best_sentence(claim: str, sentences: list):
    """Return (sentence, similarity) for the evidence sentence closest to the claim."""
    model = _get_model()
    emb_claim = model.encode(claim, convert_to_tensor=True)
    emb_sents = model.encode(sentences, convert_to_tensor=True)
    scores = util.cos_sim(emb_claim, emb_sents)[0]
    idx = int(scores.argmax())
    return sentences[idx], float(scores[idx])
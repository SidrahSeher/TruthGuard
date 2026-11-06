import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

NLI_MODEL = "cross-encoder/nli-MiniLM2-L6-H768"

_tokenizer = None
_model = None


def _load():
    """Load the model once and reuse it (loading takes a few seconds)."""
    global _tokenizer, _model
    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL)
        _model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL)
        _model.eval()
    return _tokenizer, _model


def nli_scores(premise: str, hypothesis: str) -> dict:
    """premise = evidence sentence, hypothesis = claim.
    Returns probabilities like {'contradiction': 0.02, 'entailment': 0.95, 'neutral': 0.03}."""
    tokenizer, model = _load()
    inputs = tokenizer(
        premise, hypothesis, return_tensors="pt", truncation=True, max_length=512
    )
    with torch.no_grad():
        logits = model(**inputs).logits[0]
    probs = torch.softmax(logits, dim=-1).tolist()
    labels = [model.config.id2label[i].lower() for i in range(len(probs))]
    return dict(zip(labels, probs))
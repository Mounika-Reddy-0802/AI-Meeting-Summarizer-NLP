"""ROUGE and BERTScore shared by train.py (per-epoch validation) and evaluate.py (test tables).

Scores are fractions in [0, 1]. ROUGE uses Porter stemming; ROUGE-Lsum splits text into sentences
on newlines, so predictions and references are put one sentence per line first.
"""

import re

from rouge_score import rouge_scorer

ROUGE_TYPES = ("rouge1", "rouge2", "rougeL", "rougeLsum")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _sentence_lines(text: str) -> str:
    return "\n".join(s for s in _SENTENCE_END.split(text.strip()) if s)


def rouge(predictions: list[str], references: list[str]) -> dict[str, float]:
    """Mean F-measure for ROUGE-1/2/L/Lsum over the corpus."""
    if len(predictions) != len(references):
        raise ValueError("predictions and references differ in length")
    scorer = rouge_scorer.RougeScorer(list(ROUGE_TYPES), use_stemmer=True)
    totals = dict.fromkeys(ROUGE_TYPES, 0.0)
    for pred, ref in zip(predictions, references, strict=True):
        for key, score in scorer.score(_sentence_lines(ref), _sentence_lines(pred)).items():
            totals[key] += score.fmeasure
    # plain mean, not rouge_score's bootstrap estimate, so reruns give identical numbers
    return {key: round(totals[key] / max(len(predictions), 1), 4) for key in ROUGE_TYPES}


def bertscore(
    predictions: list[str], references: list[str], model_type: str = "roberta-large", batch_size: int = 32
) -> float:
    """Mean BERTScore F1 without baseline rescaling (the bert-score default for English)."""
    from bert_score import score

    _, _, f1 = score(predictions, references, model_type=model_type, batch_size=batch_size, verbose=False)
    return round(float(f1.mean()), 4)

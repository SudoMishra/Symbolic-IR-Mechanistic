from __future__ import annotations

import re
import string
import unicodedata
from collections import Counter


def normalize_answer(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().strip()
    value = re.sub(r"[^\w.%-]+", " ", value)
    return " ".join(value.split())


def answer_exact_match(predicted: str, expected: str) -> bool:
    return normalize_answer(predicted) == normalize_answer(expected)


def answer_f1(predicted: str, expected_values: list[str] | tuple[str, ...]) -> float:
    """Maximum token F1 over accepted answer aliases."""
    predicted_tokens = normalize_answer(predicted).split()
    best = 0.0
    for expected in expected_values:
        expected_tokens = normalize_answer(expected).split()
        remaining = list(expected_tokens)
        overlap = 0
        for token in predicted_tokens:
            if token in remaining:
                overlap += 1
                remaining.remove(token)
        if not predicted_tokens or not expected_tokens:
            score = float(predicted_tokens == expected_tokens)
        elif overlap == 0:
            score = 0.0
        else:
            precision = overlap / len(predicted_tokens)
            recall = overlap / len(expected_tokens)
            score = 2 * precision * recall / (precision + recall)
        best = max(best, score)
    return best


def musique_normalize_answer(value: str) -> str:
    """Match MuSiQue's official SQuAD-style answer normalization."""
    value = value.lower()
    punctuation = set(string.punctuation)
    value = "".join(character for character in value if character not in punctuation)
    value = re.sub(r"\b(a|an|the)\b", " ", value)
    return " ".join(value.split())


def musique_answer_scores(predicted: str, expected_values: list[str] | tuple[str, ...]) -> tuple[bool, float]:
    """Return official-style maximum EM and token F1 across answer aliases."""
    predicted_normalized = musique_normalize_answer(predicted)
    predicted_tokens = predicted_normalized.split() if predicted_normalized else []
    exact = False
    best_f1 = 0.0
    for expected in expected_values:
        expected_normalized = musique_normalize_answer(expected)
        expected_tokens = expected_normalized.split() if expected_normalized else []
        exact = exact or predicted_normalized == expected_normalized
        overlap = sum((Counter(predicted_tokens) & Counter(expected_tokens)).values())
        if not predicted_tokens or not expected_tokens:
            score = float(predicted_tokens == expected_tokens)
        elif not overlap:
            score = 0.0
        else:
            precision = overlap / len(predicted_tokens)
            recall = overlap / len(expected_tokens)
            score = 2 * precision * recall / (precision + recall)
        best_f1 = max(best_f1, score)
    return exact, best_f1

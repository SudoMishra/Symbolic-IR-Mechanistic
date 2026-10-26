from __future__ import annotations

from typing import Any


def citation_scores(predicted: tuple[str, ...], expected: tuple[str, ...]) -> dict[str, Any]:
    predicted_set, expected_set = set(predicted), set(expected)
    overlap = len(predicted_set & expected_set)
    precision = overlap / len(predicted_set) if predicted_set else (1.0 if not expected_set else 0.0)
    recall = overlap / len(expected_set) if expected_set else 1.0
    return {
        "citation_exact_match": predicted_set == expected_set,
        "citation_precision": precision,
        "citation_recall": recall,
    }


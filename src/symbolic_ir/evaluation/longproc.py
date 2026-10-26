"""LongProc Theory-of-Mind trace evaluation.

The trace metrics reproduce the Apache-2.0 LongProc evaluator.  The final-answer
metric is an additional diagnostic because the official trace metric ignores it.
"""

from __future__ import annotations

import re
import string
from typing import Any


_ARTICLES = re.compile(
    r"\b(a|an|the|on|in|at|step|thinks|think|believes|believe|is|are|of|location|know|knows|belief)\b"
)


def normalize_tom(text: str) -> str:
    text = text.lower()
    text = "".join(character for character in text if character not in string.punctuation and character != "’")
    return " ".join(_ARTICLES.sub(" ", text).split())


def extract_beliefs(text: str) -> list[str]:
    beliefs = []
    for line in text.strip().splitlines():
        line = line.strip()
        if line.startswith("-"):
            beliefs.append(normalize_tom(line.split("-", 1)[1].strip()))
    return beliefs


def _extract_final_answer(text: str) -> str | None:
    matches = re.findall(r"^\s*final\s+answer\s*:\s*(.+?)\s*$", text, flags=re.IGNORECASE | re.MULTILINE)
    return matches[-1] if matches else None


def evaluate_tom_trace(prediction: str, reference: str) -> dict[str, Any]:
    predicted = extract_beliefs(prediction)
    expected = extract_beliefs(reference)
    if not expected:
        raise ValueError("LongProc reference contains no belief-trace lines")

    first_difference = next(
        (index for index, pair in enumerate(zip(predicted, expected)) if pair[0] != pair[1]),
        None,
    )
    exact = len(predicted) == len(expected) and first_difference is None
    if exact:
        partial = 1.0
        error_report = None
    elif first_difference is not None:
        partial = first_difference / len(expected)
        error_report = {
            "line": first_difference,
            "prediction": predicted[first_difference],
            "reference": expected[first_difference],
        }
    else:
        partial = min(len(predicted), len(expected)) / len(expected)
        error_report = {
            "line": min(len(predicted), len(expected)),
            "prediction": None if len(predicted) <= len(expected) else predicted[len(expected)],
            "reference": None if len(expected) <= len(predicted) else expected[len(predicted)],
        }

    predicted_final = _extract_final_answer(prediction)
    reference_final = _extract_final_answer(reference)
    final_exact = bool(
        predicted_final is not None
        and reference_final is not None
        and normalize_tom(predicted_final) == normalize_tom(reference_final)
    )
    return {
        "accuracy": float(exact),
        "partial_accuracy": partial,
        "extraction_rate": 1.0,
        "final_answer_accuracy": float(final_exact),
        "predicted_steps": len(predicted),
        "reference_steps": len(expected),
        "predicted_final_answer": predicted_final,
        "reference_final_answer": reference_final,
        "error_report": error_report,
    }

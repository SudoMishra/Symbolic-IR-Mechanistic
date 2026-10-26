from __future__ import annotations

import math
from typing import Sequence


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must have equal length")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def centered_kernel_alignment(left, right) -> float:
    """Linear CKA for 2-D arrays; NumPy is loaded only when requested."""
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Install llm-symbolic-ir[analysis] for CKA") from exc
    x, y = np.asarray(left), np.asarray(right)
    if x.ndim != 2 or y.ndim != 2 or x.shape[0] != y.shape[0]:
        raise ValueError("Inputs must be 2-D with the same number of observations")
    x = x - x.mean(axis=0, keepdims=True)
    y = y - y.mean(axis=0, keepdims=True)
    numerator = np.linalg.norm(x.T @ y, "fro") ** 2
    denominator = np.linalg.norm(x.T @ x, "fro") * np.linalg.norm(y.T @ y, "fro")
    return float(numerator / denominator) if denominator else 0.0


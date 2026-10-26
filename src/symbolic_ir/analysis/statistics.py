"""Dependency-free paired bootstrap confidence intervals."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class PairedEffect:
    condition_a: str
    condition_b: str
    metric: str
    n_pairs: int
    mean_delta: float
    ci_low: float
    ci_high: float


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def paired_bootstrap(
    records: Iterable[dict[str, Any]], condition_a: str, condition_b: str,
    metric: str = "citation_exact_match", *, samples: int = 10_000, seed: int = 0,
    extractor: Callable[[dict[str, Any]], float] | None = None,
) -> PairedEffect:
    extractor = extractor or (lambda row: float(row["evaluation"][metric]))
    paired: dict[tuple, dict[str, float]] = {}
    for row in records:
        condition = row.get("identifier_condition")
        if condition not in (condition_a, condition_b):
            continue
        key = (row["example_id"], row.get("reasoning_budget"), row.get("require_citations", True))
        paired.setdefault(key, {})[condition] = extractor(row)
    deltas = [values[condition_b] - values[condition_a] for values in paired.values() if condition_a in values and condition_b in values]
    if not deltas:
        raise ValueError("No matched pairs found")
    rng = random.Random(seed)
    boot = [sum(rng.choice(deltas) for _ in deltas) / len(deltas) for _ in range(samples)]
    return PairedEffect(
        condition_a=condition_a, condition_b=condition_b, metric=metric, n_pairs=len(deltas),
        mean_delta=sum(deltas) / len(deltas), ci_low=_percentile(boot, 0.025), ci_high=_percentile(boot, 0.975),
    )


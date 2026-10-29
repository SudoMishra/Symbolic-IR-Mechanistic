"""Statistical helpers for frontier evaluations."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from symbolic_ir.analysis.statistics import _percentile


@dataclass(frozen=True)
class BootstrapDeltaResult:
    mean_delta: float
    ci_low: float
    ci_high: float
    n_pairs: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_delta": round(self.mean_delta, 4),
            "ci_low": round(self.ci_low, 4),
            "ci_high": round(self.ci_high, 4),
            "mean_delta_pct": round(self.mean_delta * 100.0, 2),
            "ci_low_pct": round(self.ci_low * 100.0, 2),
            "ci_high_pct": round(self.ci_high * 100.0, 2),
            "n_pairs": self.n_pairs,
        }


def paired_bootstrap_delta(
    b: list[float],
    a: list[float],
    samples: int = 10_000,
    seed: int = 202620,
) -> BootstrapDeltaResult:
    if len(b) != len(a):
        raise ValueError(f"Arrays must have same length: {len(b)} != {len(a)}")
    if not b:
        return BootstrapDeltaResult(0.0, 0.0, 0.0, 0)
    deltas = [vb - va for vb, va in zip(b, a)]
    mean_d = sum(deltas) / len(deltas)
    rng = random.Random(seed)
    boot = [sum(rng.choice(deltas) for _ in deltas) / len(deltas) for _ in range(samples)]
    return BootstrapDeltaResult(
        mean_delta=mean_d,
        ci_low=_percentile(boot, 0.025),
        ci_high=_percentile(boot, 0.975),
        n_pairs=len(deltas),
    )

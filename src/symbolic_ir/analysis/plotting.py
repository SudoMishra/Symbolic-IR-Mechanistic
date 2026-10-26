"""Optional plotting helpers; tabular analysis does not require matplotlib."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def plot_metric(summary: list[dict[str, Any]], metric: str, output: str | Path) -> Path:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Install llm-symbolic-ir[analysis] to create plots") from exc
    labels = [f"{row['identifier_condition']}\nN={row['num_sources']}" for row in summary]
    values = [row.get(metric) or 0.0 for row in summary]
    figure, axis = plt.subplots(figsize=(max(6, len(labels) * 0.8), 4))
    axis.bar(labels, values)
    axis.set_ylabel(metric.replace("_", " ").title())
    axis.set_ylim(0, 1 if "accuracy" in metric or "rate" in metric else None)
    axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)
    return path


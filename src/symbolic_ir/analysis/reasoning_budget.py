from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def budget_curves(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[(row["identifier_condition"], row.get("reasoning_budget"))].append(row)
    curves = []
    for (condition, budget), rows in sorted(grouped.items(), key=lambda item: str(item[0])):
        citations = [row["evaluation"]["citation_exact_match"] for row in rows if row["evaluation"]["citation_exact_match"] is not None]
        reasoning = [row["token_counts"]["reasoning"] for row in rows if row["token_counts"].get("reasoning") is not None]
        curves.append({
            "identifier_condition": condition, "reasoning_budget": budget, "n": len(rows),
            "answer_accuracy": sum(row["evaluation"]["answer_correct"] for row in rows) / len(rows),
            "citation_accuracy": sum(citations) / len(citations) if citations else None,
            "mean_reasoning_tokens": sum(reasoning) / len(reasoning) if reasoning else None,
        })
    return curves


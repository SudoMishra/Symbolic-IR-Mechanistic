from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def aggregate_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = (
            record.get("identifier_condition"), record.get("task_type"),
            len(record.get("source_order", [])), record.get("reasoning_budget"),
            record.get("require_citations", True),
        )
        groups[key].append(record)
    output = []
    for key, rows in sorted(groups.items(), key=lambda item: str(item[0])):
        answer_correct = [float(row["evaluation"]["answer_correct"]) for row in rows]
        citation_rows = [row for row in rows if row["evaluation"]["citation_exact_match"] is not None]
        correct_answer_rows = [row for row in citation_rows if row["evaluation"]["answer_correct"]]
        taxonomy = Counter(row["evaluation"]["failure_category"] for row in rows)
        output.append({
            "identifier_condition": key[0], "task_type": key[1], "num_sources": key[2],
            "reasoning_budget": key[3], "require_citations": key[4], "n": len(rows),
            "answer_accuracy": _mean(answer_correct),
            "citation_accuracy": _mean([float(row["evaluation"]["citation_exact_match"]) for row in citation_rows]),
            "citation_precision": _mean([float(row["evaluation"]["citation_precision"]) for row in citation_rows]),
            "citation_recall": _mean([float(row["evaluation"]["citation_recall"]) for row in citation_rows]),
            "citation_given_correct_answer": _mean([float(row["evaluation"]["citation_exact_match"]) for row in correct_answer_rows]),
            "invalid_id_rate": _mean([float(row["evaluation"]["invalid_id_rate"]) for row in rows]),
            "malformed_id_rate": _mean([float(row["evaluation"]["malformed_id_rate"]) for row in rows]),
            "mean_input_tokens": _mean([float(row["token_counts"]["input"]) for row in rows if row["token_counts"].get("input") is not None]),
            "mean_output_tokens": _mean([float(row["token_counts"]["output"]) for row in rows if row["token_counts"].get("output") is not None]),
            "mean_reasoning_tokens": _mean([float(row["token_counts"]["reasoning"]) for row in rows if row["token_counts"].get("reasoning") is not None]),
            "mean_latency_seconds": _mean([float(row["latency"]) for row in rows if row.get("latency") is not None]),
            "failure_counts": dict(sorted(taxonomy.items())),
        })
    return output


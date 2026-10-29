"""Statistical analysis and reporting for Phase 2 MuSiQue Frontier evaluations."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.statistics import paired_bootstrap_delta  # noqa: E402


def analyze_frontier_file(file_path: Path) -> dict[str, Any]:
    records = [json.loads(line) for line in file_path.read_text(encoding="utf-8").splitlines() if line]
    by_cell = defaultdict(list)
    for r in records:
        eval_data = r.get("evaluation", {})
        tokens = r.get("token_counts", {})
        cond = r.get("condition") or r.get("identifier_condition")
        ns = r.get("num_sources")
        by_cell[(ns, cond)].append({
            "example_id": r.get("example_id"),
            "answer_correct": eval_data.get("answer_correct", False),
            "citation_exact_match": eval_data.get("citation_exact_match", False),
            "citation_precision": eval_data.get("citation_precision", 0.0),
            "citation_recall": eval_data.get("citation_recall", 0.0),
            "strict_format": eval_data.get("strict_format", False),
            "parsed_answer": eval_data.get("parsed_answer"),
            "failure_category": eval_data.get("failure_category", "unknown"),
            "input_tokens": int(tokens.get("input") or 0),
            "output_tokens": int(tokens.get("output") or 0),
            "reasoning_tokens": int(tokens.get("reasoning") or 0),
            "calculated_cost": float(r.get("calculated_cost") or 0.0),
            "stop_reason": r.get("stop_reason"),
        })

    summary: dict[str, Any] = {}
    for (ns, cond), items in by_cell.items():
        n = len(items)
        if n == 0:
            continue
        acc = sum(1 for it in items if it["answer_correct"]) / n
        cem = sum(1 for it in items if it["citation_exact_match"]) / n
        prec = sum(float(it["citation_precision"] or 0) for it in items) / n
        rec = sum(float(it["citation_recall"] or 0) for it in items) / n
        strict = sum(1 for it in items if it["strict_format"]) / n
        summary[f"{ns}_{cond}"] = {
            "n": n,
            "answer_accuracy": round(acc * 100.0, 2),
            "citation_exact_match": round(cem * 100.0, 2),
            "citation_precision": round(prec * 100.0, 2),
            "citation_recall": round(rec * 100.0, 2),
            "strict_format_rate": round(strict * 100.0, 2),
            "mean_input_tokens": round(sum(it["input_tokens"] for it in items) / n, 1),
            "mean_output_tokens": round(sum(it["output_tokens"] for it in items) / n, 1),
            "mean_reasoning_tokens": round(sum(it["reasoning_tokens"] for it in items) / n, 1),
            "max_tokens_rate": round(
                sum(1 for it in items if it["stop_reason"] == "max_tokens") / n * 100.0,
                2,
            ),
            "calculated_cost": round(sum(it["calculated_cost"] for it in items), 6),
        }

    # Paired deltas (UUID - numeric)
    deltas = {}
    for ns in [15, 20]:
        num_items = {it["example_id"]: it for it in by_cell.get((ns, "numeric"), [])}
        uuid_items = {it["example_id"]: it for it in by_cell.get((ns, "uuid"), [])}
        common = sorted(set(num_items.keys()) & set(uuid_items.keys()))
        if common:
            acc_num = [1.0 if num_items[k]["answer_correct"] else 0.0 for k in common]
            acc_uuid = [1.0 if uuid_items[k]["answer_correct"] else 0.0 for k in common]
            acc_boot = paired_bootstrap_delta(acc_uuid, acc_num, seed=202620)

            cem_num = [1.0 if num_items[k]["citation_exact_match"] else 0.0 for k in common]
            cem_uuid = [1.0 if uuid_items[k]["citation_exact_match"] else 0.0 for k in common]
            cem_boot = paired_bootstrap_delta(cem_uuid, cem_num, seed=202620)

            recall_num = [float(num_items[k]["citation_recall"] or 0.0) for k in common]
            recall_uuid = [float(uuid_items[k]["citation_recall"] or 0.0) for k in common]
            recall_boot = paired_bootstrap_delta(recall_uuid, recall_num, seed=202620)

            deltas[f"{ns}_sources"] = {
                "paired_count": len(common),
                "answer_accuracy_delta": acc_boot.to_dict(),
                "citation_exact_match_delta": cem_boot.to_dict(),
                "citation_recall_delta": recall_boot.to_dict(),
            }

    return {
        "records": len(records),
        "calculated_cost": round(sum(float(r.get("calculated_cost") or 0.0) for r in records), 6),
        "cells": summary,
        "deltas": deltas,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True)
    args = parser.parse_args()
    res = analyze_frontier_file(Path(args.file))
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Analyze the Stage 5 explicit reasoning-budget experiment."""

from __future__ import annotations

import argparse
import glob
import json
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def arm(row: dict[str, Any]) -> str:
    if row["identifier_condition"] == "uuid" and not row["require_citations"]:
        return "uuid_no_reproduction"
    return row["identifier_condition"]


def citation_field(output: str) -> str:
    match = re.search(r"(?im)^\s*CITATIONS?\s*:\s*(.*?)\s*$", output)
    return match.group(1) if match else ""


def binding_recall(row: dict[str, Any]) -> float | None:
    if not row["require_citations"]:
        return None
    text, found = citation_field(row["raw_output"]), set()
    for source, label in row["identifier_mapping"]["citation_by_source"].items():
        inner = label[1:-1] if label[:1] in "[<" and label[-1:] in "]>" else label
        if label in text or re.search(r"(?<![A-Za-z0-9])" + re.escape(inner) + r"(?![A-Za-z0-9])", text, re.I):
            found.add(source)
    expected = set(row["relevant_sources"])
    return len(found & expected) / len(expected) if expected else 0.0


def citation_f1(row: dict[str, Any]) -> float | None:
    precision, recall = row["evaluation"]["citation_precision"], row["evaluation"]["citation_recall"]
    if precision is None or recall is None:
        return None
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


METRICS: dict[str, Callable[[dict[str, Any]], float | None]] = {
    "answer_accuracy": lambda row: float(row["evaluation"]["answer_correct"]),
    "answer_f1": lambda row: float(row["evaluation"]["answer_f1"]),
    "binding_recall": binding_recall,
    "citation_f1": citation_f1,
    "malformed_id": lambda row: None if not row["require_citations"] else float(row["evaluation"]["malformed_id_rate"]),
    "invalid_id": lambda row: None if not row["require_citations"] else float(row["evaluation"]["invalid_id_rate"]),
    "reasoning_tokens": lambda row: float(row["token_counts"]["reasoning_output"] or 0),
    "total_output_tokens": lambda row: float(row["token_counts"]["total_output"]),
    "reasoning_cap_hit": lambda row: float(row["reasoning_cap_hit"]),
}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"n": len(rows)}
    for name, function in METRICS.items():
        values = [value for row in rows if (value := function(row)) is not None]
        result[name] = mean(values) if values else None
    result["mean_prompt_tokens"] = mean([float(row["token_counts"]["validated_reasoning_input"]) for row in rows])
    result["mean_latency_seconds"] = mean([float(row["latency"]["total"]) for row in rows])
    return result


def paired(rows: list[dict[str, Any]], left_arm: str, right_arm: str, metric: str) -> dict[str, Any]:
    def keyed(target: str) -> dict[tuple[Any, ...], dict[str, Any]]:
        return {
            (row["example_id"], row["reasoning_budget"]): row for row in rows if arm(row) == target
        }
    left, right = keyed(left_arm), keyed(right_arm)
    keys = sorted(left.keys() & right.keys())
    deltas = []
    for key in keys:
        a, b = METRICS[metric](left[key]), METRICS[metric](right[key])
        if a is not None and b is not None:
            deltas.append(float(b) - float(a))
    if not deltas:
        return {"left": left_arm, "right": right_arm, "metric": metric, "n_pairs": 0}
    rng = random.Random(202605 + len(metric) + len(left_arm) * 11)
    bootstrap = [mean([rng.choice(deltas) for _ in deltas]) for _ in range(10_000)]
    return {"left": left_arm, "right": right_arm, "metric": metric, "n_pairs": len(deltas),
            "right_minus_left": mean(deltas),
            "bootstrap_95_ci": [percentile(bootstrap, 0.025), percentile(bootstrap, 0.975)]}


def analyze_model(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cells = []
    for task in sorted({row["task_type"] for row in rows}):
        for sources in sorted({int(row["dataset_cell"]["num_sources"]) for row in rows}):
            for budget in sorted({int(row["reasoning_budget"]) for row in rows}):
                for label in ("numeric", "random_compact", "uuid", "uuid_no_reproduction"):
                    selected = [row for row in rows if row["task_type"] == task
                                and int(row["dataset_cell"]["num_sources"]) == sources
                                and int(row["reasoning_budget"]) == budget and arm(row) == label]
                    if selected:
                        cells.append({"task": task, "sources": sources, "budget": budget,
                                      "arm": label, **summarize(selected)})
    effects = []
    for sources in sorted({int(row["dataset_cell"]["num_sources"]) for row in rows}):
        for budget in sorted({int(row["reasoning_budget"]) for row in rows}):
            selected = [row for row in rows if int(row["dataset_cell"]["num_sources"]) == sources
                        and int(row["reasoning_budget"]) == budget]
            for comparison in (("numeric", "uuid"), ("uuid", "uuid_no_reproduction")):
                for metric in ("answer_accuracy", "answer_f1", "binding_recall", "citation_f1",
                               "reasoning_tokens", "total_output_tokens"):
                    effect = paired(selected, *comparison, metric)
                    effect.update({"sources": sources, "budget": budget})
                    effects.append(effect)
    return {"model": rows[0]["model"], "model_revision": rows[0]["model_revision"],
            "records": len(rows), "overall": summarize(rows), "cells": cells, "effects": effects}


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.1f}%"


def report(result: dict[str, Any]) -> str:
    lines = ["# Stage 5: explicit reasoning-budget findings", "",
             f"**Design:** {result['records']} two-pass generations across {len(result['models'])} model(s). "
             "The first pass receives the 2k–4k-token source prompt and a hard scratchpad cap; the second pass receives "
             "only that scratchpad and a fixed 128-token final-answer cap.", "",
             "This manipulates visible scratchpad/output capacity. It is not a measurement of proprietary hidden reasoning tokens.", "",
             "## Aggregate accuracy and token use", "",
             "| Model | Budget | Numeric acc. | Compact acc. | UUID acc. | UUID no-reproduction acc. | Numeric reasoning tok. | UUID reasoning tok. | UUID cap-hit |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for model in result["models"]:
        budgets = sorted({cell["budget"] for cell in model["cells"]})
        for budget in budgets:
            grouped = {}
            for label in ("numeric", "random_compact", "uuid", "uuid_no_reproduction"):
                selected = [row for row in model["raw_rows"] if int(row["reasoning_budget"]) == budget and arm(row) == label]
                grouped[label] = summarize(selected)
            lines.append(
                f"| {model['model']} | {budget} | {pct(grouped['numeric']['answer_accuracy'])} | "
                f"{pct(grouped['random_compact']['answer_accuracy'])} | {pct(grouped['uuid']['answer_accuracy'])} | "
                f"{pct(grouped['uuid_no_reproduction']['answer_accuracy'])} | "
                f"{grouped['numeric']['reasoning_tokens']:.1f} | {grouped['uuid']['reasoning_tokens']:.1f} | "
                f"{pct(grouped['uuid']['reasoning_cap_hit'])} |"
            )
    lines.extend(("", "## Calibration by task", "",
                  "| Model | Task | Accuracy across all arms/budgets |", "|---|---|---:|"))
    for model in result["models"]:
        for task in sorted({row["task_type"] for row in model["raw_rows"]}):
            lines.append(f"| {model['model']} | {task} | {pct(summarize([row for row in model['raw_rows'] if row['task_type'] == task])['answer_accuracy'])} |")
    lines.extend(("", "## Interpretation", "",
                  "The machine-readable result contains paired bootstrap intervals for UUID versus numeric and for UUID citation reproduction versus no reproduction at every source-count/budget cell.",
                  "Tasks or cells outside the target 30–70% accuracy band should be recalibrated before the full model matrix.", ""))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_jsonl", nargs="*")
    parser.add_argument("--json-output", default="results/processed/stage5.json")
    parser.add_argument("--report-output", default="FINDINGS_STAGE5.md")
    args = parser.parse_args()
    paths = [Path(path) for path in args.raw_jsonl] or [Path(path) for path in sorted(glob.glob("results/raw/stage5_*/*.jsonl"))]
    rows = [json.loads(line) for path in paths for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["model"]].append(row)
    models = []
    for _, items in sorted(grouped.items()):
        analysis = analyze_model(items)
        analysis["raw_rows"] = items
        models.append(analysis)
    result = {"records": len(rows), "models": models, "raw_results": [str(path) for path in paths]}
    report_text = report(result)
    serializable = {**result, "models": [{key: value for key, value in model.items() if key != "raw_rows"} for model in models]}
    json_path, report_path = Path(args.json_output), Path(args.report_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(serializable, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(report_text, encoding="utf-8")
    print(json.dumps({"records": len(rows), "models": len(models), "json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

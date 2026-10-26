#!/usr/bin/env python3
"""Analyze Stage 8 synthetic entity canonicalization."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


CONDITIONS = ("raw", "random_masked", "untyped", "typed")
BOOTSTRAPS = 5_000


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def entity_pattern(condition: str) -> str:
    patterns = {
        "raw": r"ACC-\d{12}",
        "random_masked": r"<[A-F0-9]{6}>",
        "untyped": r"<ENTITY_\d+>",
        "typed": r"<(?:PERSON|EMAIL|ACCOUNT|PHONE|ADDRESS|URL)_\d+>",
    }
    return patterns[condition]


def entity_candidates(row: dict[str, Any]) -> set[str]:
    return {
        normalize(value) for value in re.findall(
            entity_pattern(row["identifier_condition"]), row["prompt"]
        )
    }


def enrich(row: dict[str, Any]) -> dict[str, Any]:
    correct = bool(row["evaluation"]["answer_correct"])
    candidates = entity_candidates(row)
    predicted_handles = {
        normalize(value) for value in re.findall(
            entity_pattern(row["identifier_condition"]), row["parsed_answer"]
        )
    }
    if not predicted_handles:
        # Models often omit angle brackets while preserving the handle.
        relaxed = entity_pattern(row["identifier_condition"]).replace("<", "<?").replace(">", ">?")
        predicted_handles = {normalize(value) for value in re.findall(relaxed, row["parsed_answer"])}
    wrong_existing = bool(predicted_handles) and not correct and predicted_handles <= candidates
    hallucinated = bool(predicted_handles) and not correct and bool(predicted_handles - candidates)
    invalid_output = not correct and not predicted_handles
    row = dict(row)
    row["analysis"] = {
        "task_accuracy": float(correct),
        "entity_binding_accuracy": float(correct),
        "wrong_existing_entity": float(wrong_existing),
        "hallucinated_entity": float(hallucinated),
        "invalid_entity_output": float(invalid_output),
        "any_raw_pii_leakage": float(row["evaluation"]["raw_pii_leakage_rate"] > 0),
        "literal_surface_exact": float(row["parsed_answer"].strip() == row["evaluation"]["expected_answer"].strip()),
    }
    return row


def interval(values, seed: int) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(array), size=(BOOTSTRAPS, len(array)))
    draws = array[indices].mean(axis=1)
    return {
        "n": len(array), "mean": float(array.mean()),
        "bootstrap_95_ci": [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))],
        "bootstrap_replicates": BOOTSTRAPS,
    }


def exact_p(discordant_a: int, discordant_b: int) -> float:
    total = discordant_a + discordant_b
    if total == 0:
        return 1.0
    tail = sum(math.comb(total, index) for index in range(0, min(discordant_a, discordant_b) + 1)) / 2**total
    return min(1.0, 2 * tail)


def paired(rows, left: str, right: str, extractor, seed: int):
    grouped = defaultdict(dict)
    for row in rows:
        grouped[(row["example_id"], row["dataset_cell"]["num_sources"])][row["identifier_condition"]] = row
    pairs = [(values[left], values[right]) for values in grouped.values() if left in values and right in values]
    deltas = [extractor(right_row) - extractor(left_row) for left_row, right_row in pairs]
    summary = interval(deltas, seed)
    left_only = sum(extractor(a) > extractor(b) for a, b in pairs)
    right_only = sum(extractor(b) > extractor(a) for a, b in pairs)
    summary.update({
        "condition_a": left, "condition_b": right,
        "delta_definition": f"{right}_minus_{left}",
        "left_only_better": left_only, "right_only_better": right_only,
        "mcnemar_exact_p": exact_p(left_only, right_only),
    })
    return summary


def analyze(path: Path):
    rows = [enrich(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    grouped = defaultdict(list)
    for row in rows:
        grouped[(int(row["dataset_cell"]["num_sources"]), row["identifier_condition"])].append(row)
    cells = []
    for (sources, condition), selected in sorted(grouped.items()):
        cells.append({
            "num_sources": sources, "condition": condition, "n": len(selected),
            "task_accuracy": float(np.mean([row["analysis"]["task_accuracy"] for row in selected])),
            "answer_f1": float(np.mean([row["evaluation"]["answer_f1"] for row in selected])),
            "wrong_existing_entity_rate": float(np.mean([row["analysis"]["wrong_existing_entity"] for row in selected])),
            "hallucinated_entity_rate": float(np.mean([row["analysis"]["hallucinated_entity"] for row in selected])),
            "invalid_entity_output_rate": float(np.mean([row["analysis"]["invalid_entity_output"] for row in selected])),
            "any_raw_pii_leakage_rate": float(np.mean([row["analysis"]["any_raw_pii_leakage"] for row in selected])),
            "literal_surface_exact_rate": float(np.mean([row["analysis"]["literal_surface_exact"] for row in selected])),
            "mean_input_tokens": float(np.mean([row["token_counts"]["input"] for row in selected])),
            "mean_output_tokens": float(np.mean([row["token_counts"]["output"] for row in selected])),
            "mean_latency_seconds": float(np.mean([row["latency"] for row in selected])),
        })
    seed = 808000
    effects = {}
    for left, right in (("untyped", "typed"), ("random_masked", "typed"), ("raw", "typed")):
        seed += 1
        effects[f"{right}_vs_{left}_accuracy"] = paired(
            rows, left, right, lambda row: row["analysis"]["task_accuracy"], seed
        )
        seed += 1
        effects[f"{right}_vs_{left}_input_tokens"] = paired(
            rows, left, right, lambda row: float(row["token_counts"]["input"]), seed
        )
    return {
        "path": str(path), "records": len(rows),
        "semantic_examples": len(set(row["example_id"] for row in rows)),
        "model": rows[0]["model"], "model_revision": rows[0]["model_revision"],
        "cells": cells, "paired_effects": effects,
        "synthetic_only": True, "source_identifiers_fixed": "structured",
    }


def cell(result, sources, condition):
    return next(value for value in result["cells"]
                if value["num_sources"] == sources and value["condition"] == condition)


def pct(value):
    return f"{100 * value:.1f}%"


def report(result):
    lines = [
        "# Stage 8: synthetic PII and entity canonicalization", "",
        f"**Design:** {result['semantic_examples']} synthetic account-resolution examples × four entity "
        f"representations = {result['records']} deterministic generations through `{result['model']}`. "
        "Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer "
        "mapping; only entity surface form changes. Citations are not requested.", "",
        "| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for sources in sorted({value["num_sources"] for value in result["cells"]}):
        for condition in CONDITIONS:
            value = cell(result, sources, condition)
            lines.append(
                f"| {sources} | {condition} | {pct(value['task_accuracy'])} | "
                f"{pct(value['wrong_existing_entity_rate'])} | {pct(value['hallucinated_entity_rate'])} | "
                f"{pct(value['invalid_entity_output_rate'])} | {pct(value['any_raw_pii_leakage_rate'])} | "
                f"{value['mean_input_tokens']:.1f} | "
                f"{value['mean_output_tokens']:.1f} | {value['mean_latency_seconds']:.2f}s |"
            )
    lines.extend(("", "## Paired effects", "",
                  "Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.", "",
                  "| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |",
                  "|---|---:|---:|---:|---:|"))
    for left, right in (("untyped", "typed"), ("random_masked", "typed"), ("raw", "typed")):
        accuracy = result["paired_effects"][f"{right}_vs_{left}_accuracy"]
        tokens = result["paired_effects"][f"{right}_vs_{left}_input_tokens"]
        low, high = accuracy["bootstrap_95_ci"]
        lines.append(
            f"| {right} − {left} | {100*accuracy['mean']:+.1f} pp "
            f"[{100*low:+.1f}, {100*high:+.1f}] | {accuracy['left_only_better']}/{accuracy['right_only_better']} | "
            f"{accuracy['mcnemar_exact_p']:.3g} | {tokens['mean']:+.1f} |"
        )
    effect = result["paired_effects"]["typed_vs_untyped_accuracy"]
    low, high = effect["bootstrap_95_ci"]
    gate = effect["mean"] > 0 and effect["mcnemar_exact_p"] < 0.05
    lines.extend(("", "## Checkpoint 8", "",
                  f"**Decision: {'generalization signal present' if gate else 'no confirmed improvement yet'}.** "
                  f"Typed minus untyped accuracy is {100*effect['mean']:+.1f} pp "
                  f"(95% CI [{100*low:+.1f}, {100*high:+.1f}]) while holding source labels fixed. "
                  "All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.", ""))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-report", required=True)
    args = parser.parse_args()
    result = analyze(Path(args.input))
    json_path, report_path = Path(args.output_json), Path(args.output_report)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(report(result), encoding="utf-8")
    print(json.dumps(result["paired_effects"]["typed_vs_untyped_accuracy"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Analyze Stage 5 explicit reasoning-budget scaling across all 8 models."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

BUDGETS = (64, 128, 256, 512, 1024)
ARMS = ("numeric", "random_compact", "uuid", "uuid_no_reproduction")
BOOTSTRAPS = 10_000

MODEL_PATHS = {
    "Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m": Path("results/raw/stage5_pilot_qwen25_15b/61443c6b5233.jsonl"),
    "unsloth/Qwen3.5-2B-GGUF:q4_k_m": Path("results/raw/stage5_pilot_qwen35_2b/b3b211daeedf.jsonl"),
    "unsloth/Qwen3.5-4B-GGUF:q4_k_m": Path("results/raw/stage5_pilot_qwen35_4b/9f3862caafba.jsonl"),
    "LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m": Path("results/raw/stage5_pilot_lfm25_12b/bfb75a3ec7dd.jsonl"),
    "LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m": Path("results/raw/stage5_pilot_lfm25_26b/a816243d2fff.jsonl"),
    "google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0": Path("results/raw/stage5_pilot_gemma4_e2b/400c508d5acb.jsonl"),
    "google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0": Path("results/raw/stage5_pilot_gemma4_e4b/c4931b820baf.jsonl"),
    "CohereLabs/tiny-aya-global-GGUF:q4_k_m": Path("results/raw/stage5_pilot_tiny_aya_global/32fa0c3c696f.jsonl"),
}


def arm(row: dict[str, Any]) -> str:
    if row["identifier_condition"] == "uuid" and not row["require_citations"]:
        return "uuid_no_reproduction"
    return str(row["identifier_condition"])


def accuracy(row: dict[str, Any]) -> float:
    return float(row["evaluation"]["answer_correct"])


def paired_bootstrap_difference(
    blocks: list[dict[tuple[str, int], float]],
    arm_a: str,
    arm_b: str,
    budget: int,
    bootstraps: int = BOOTSTRAPS,
    seed: int = 202607,
) -> dict[str, Any]:
    diffs = []
    for b in blocks:
        if (arm_a, budget) in b and (arm_b, budget) in b:
            diffs.append(b[(arm_a, budget)] - b[(arm_b, budget)])
    if not diffs:
        return {"estimate": 0.0, "bootstrap_95_ci": [0.0, 0.0], "n": 0}
    estimate = mean(diffs)
    rng = random.Random(seed)
    n = len(diffs)
    samples = []
    for _ in range(bootstraps):
        resampled = [diffs[rng.randrange(n)] for _ in range(n)]
        samples.append(mean(resampled))
    samples.sort()
    low = samples[int(0.025 * bootstraps)]
    high = samples[int(0.975 * bootstraps)]
    return {
        "estimate": estimate,
        "bootstrap_95_ci": [low, high],
        "n": n,
    }


def analyze_model(rows: list[dict[str, Any]], seed: int = 202607) -> dict[str, Any]:
    # Group by example block: (task_type, num_sources, example_id)
    blocks: dict[tuple[Any, ...], dict[tuple[str, int], float]] = defaultdict(dict)
    by_arm_budget: dict[tuple[str, int], list[float]] = defaultdict(list)
    by_task: dict[str, list[float]] = defaultdict(list)
    by_budget: dict[int, list[float]] = defaultdict(list)

    for row in rows:
        a = arm(row)
        b = int(row["reasoning_budget"])
        acc = accuracy(row)
        key = (row["task_type"], int(row["dataset_cell"]["num_sources"]), row["example_id"])
        blocks[key][(a, b)] = acc
        by_arm_budget[(a, b)].append(acc)
        by_task[row["task_type"]].append(acc)
        by_budget[b].append(acc)

    block_list = list(blocks.values())

    budget_stats = {}
    for b in BUDGETS:
        uuid_minus_num = paired_bootstrap_difference(block_list, "uuid", "numeric", b, seed=seed)
        no_rep_minus_uuid = paired_bootstrap_difference(block_list, "uuid_no_reproduction", "uuid", b, seed=seed)
        budget_stats[str(b)] = {
            "numeric_accuracy": mean(by_arm_budget.get(("numeric", b), [0.0])),
            "random_compact_accuracy": mean(by_arm_budget.get(("random_compact", b), [0.0])),
            "uuid_accuracy": mean(by_arm_budget.get(("uuid", b), [0.0])),
            "uuid_no_reproduction_accuracy": mean(by_arm_budget.get(("uuid_no_reproduction", b), [0.0])),
            "uuid_minus_numeric_accuracy": uuid_minus_num,
            "no_reproduction_minus_uuid_accuracy": no_rep_minus_uuid,
            "overall_accuracy": mean(by_budget.get(b, [0.0])),
        }

    task_stats = {t: mean(vals) for t, vals in sorted(by_task.items())}
    overall_acc = mean([acc for vals in by_task.values() for acc in vals])

    # Category
    if overall_acc < 0.25:
        regime = "floor"
    elif overall_acc > 0.70:
        regime = "ceiling"
    else:
        regime = "active_scaling"

    return {
        "regime": regime,
        "overall_accuracy": overall_acc,
        "task_accuracy": task_stats,
        "budgets": budget_stats,
        "records": len(rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/processed/stage5_eight_model.json")
    args = parser.parse_args()

    results: dict[str, Any] = {"models": {}}
    for model_name, path in MODEL_PATHS.items():
        if not path.exists():
            print(f"Skipping {model_name} (path {path} does not exist yet)")
            continue
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(f"Analyzing {model_name}: {len(rows)} records")
        results["models"][model_name] = analyze_model(rows)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Written comprehensive 8-model analysis to {out_path}")


if __name__ == "__main__":
    main()

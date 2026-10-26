#!/usr/bin/env python3
"""Aggregate LongProc JSONL runs with deterministic uncertainty intervals."""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * probability)]


def bootstrap_mean(values: list[float], samples: int, seed: int) -> list[float]:
    generator = random.Random(seed)
    size = len(values)
    draws = [sum(values[generator.randrange(size)] for _ in range(size)) / size for _ in range(samples)]
    return [percentile(draws, 0.025), percentile(draws, 0.975)]


def wilson_interval(successes: int, total: int, z: float = 1.95996398454) -> list[float]:
    probability = successes / total
    denominator = 1 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(probability * (1 - probability) / total + z * z / (4 * total * total)) / denominator
    return [center - radius, center + radius]


def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def summarize(rows: list[dict[str, Any]], samples: int, seed: int) -> dict[str, Any]:
    evaluations = [row["evaluation"] for row in rows]
    partial = [float(item["partial_accuracy"]) for item in evaluations]
    strict = [int(item["accuracy"]) for item in evaluations]
    final = [int(item["final_answer_accuracy"]) for item in evaluations]
    output = [int(row["token_counts"]["output"]) for row in rows]
    latency = [float(row["latency"]) for row in rows]
    return {
        "n": len(rows),
        "strict_accuracy": sum(strict) / len(rows),
        "strict_accuracy_wilson_95": wilson_interval(sum(strict), len(rows)),
        "partial_accuracy_mean": statistics.mean(partial),
        "partial_accuracy_median": statistics.median(partial),
        "partial_accuracy_bootstrap_95": bootstrap_mean(partial, samples, seed),
        "final_answer_accuracy": sum(final) / len(rows),
        "final_answer_accuracy_wilson_95": wilson_interval(sum(final), len(rows)),
        "full_trace_rate": sum(
            item["predicted_steps"] >= item["reference_steps"] for item in evaluations
        ) / len(rows),
        "output_tokens": {
            "min": min(output), "mean": statistics.mean(output),
            "median": statistics.median(output), "max": max(output),
        },
        "generation_cap_rate": sum(bool(row["hit_generation_cap"]) for row in rows) / len(rows),
        "latency_seconds_mean": statistics.mean(latency),
        "latency_seconds_total": sum(latency),
        "throughput_tokens_per_second": sum(output) / sum(latency),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", nargs=2, action="append", metavar=("LABEL", "JSONL"), required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=202601)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = {
        label: summarize(load(Path(path)), args.bootstrap_samples, args.seed + index)
        for index, (label, path) in enumerate(args.model)
    }
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()

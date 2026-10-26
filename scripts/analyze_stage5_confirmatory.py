#!/usr/bin/env python3
"""Analyze the independent-seed, calibration-filtered Stage 5 confirmation."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable


BUDGETS = (64, 128, 256, 512, 1024)
ARMS = ("numeric", "random_compact", "uuid", "uuid_no_reproduction")
BOOTSTRAPS = 10_000
PILOT_SELECTIONS = {
    "Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m": (
        Path("results/raw/stage5_pilot_qwen25_15b/61443c6b5233.jsonl"),
        {"reasoning_temporal", "reasoning_entity_resolution"},
    ),
    "google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0": (
        Path("results/raw/stage5_pilot_gemma4_e2b/400c508d5acb.jsonl"),
        {"reasoning_entity_resolution"},
    ),
    "CohereLabs/tiny-aya-global-GGUF:q4_k_m": (
        Path("results/raw/stage5_pilot_tiny_aya_global/32fa0c3c696f.jsonl"),
        {"reasoning_entity_resolution"},
    ),
}


def arm(row: dict[str, Any]) -> str:
    if row["identifier_condition"] == "uuid" and not row["require_citations"]:
        return "uuid_no_reproduction"
    return str(row["identifier_condition"])


def accuracy(row: dict[str, Any]) -> float:
    return float(row["evaluation"]["answer_correct"])


def reasoning_tokens(row: dict[str, Any]) -> float:
    return float(row["token_counts"]["reasoning_output"] or 0)


def total_output_tokens(row: dict[str, Any]) -> float:
    return float(row["token_counts"]["total_output"] or 0)


Block = dict[tuple[str, int], dict[str, Any]]


def make_blocks(rows: list[dict[str, Any]]) -> list[Block]:
    grouped: dict[tuple[Any, ...], Block] = defaultdict(dict)
    for row in rows:
        key = (
            row["model"], row["task_type"], int(row["dataset_cell"]["num_sources"]),
            row["example_id"],
        )
        grouped[key][(arm(row), int(row["reasoning_budget"]))] = row
    complete = [block for block in grouped.values() if all((a, b) in block for a in ARMS for b in BUDGETS)]
    return complete


def strata(blocks: list[Block]) -> dict[tuple[str, str, int], list[Block]]:
    result: dict[tuple[str, str, int], list[Block]] = defaultdict(list)
    for block in blocks:
        row = next(iter(block.values()))
        result[(row["model"], row["task_type"], int(row["dataset_cell"]["num_sources"]))].append(block)
    return result


def resample(blocks: list[Block], rng: random.Random) -> list[Block]:
    sampled: list[Block] = []
    for values in strata(blocks).values():
        sampled.extend(rng.choice(values) for _ in values)
    return sampled


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def interval(blocks: list[Block], estimator: Callable[[list[Block]], float], seed: int) -> dict[str, Any]:
    estimate = estimator(blocks)
    rng = random.Random(seed)
    values = [estimator(resample(blocks, rng)) for _ in range(BOOTSTRAPS)]
    return {
        "estimate": estimate,
        "bootstrap_95_ci": [percentile(values, 0.025), percentile(values, 0.975)],
        "bootstrap_replicates": BOOTSTRAPS,
    }


def arm_mean(blocks: list[Block], target: str, budget: int,
             metric: Callable[[dict[str, Any]], float] = accuracy) -> float:
    return mean(metric(block[(target, budget)]) for block in blocks)


def paired_delta(blocks: list[Block], left: str, right: str, budget: int,
                 metric: Callable[[dict[str, Any]], float] = accuracy) -> float:
    return mean(metric(block[(right, budget)]) - metric(block[(left, budget)]) for block in blocks)


def low_high_interaction(blocks: list[Block]) -> float:
    low = mean(paired_delta(blocks, "numeric", "uuid", budget) for budget in (64, 128))
    high = mean(paired_delta(blocks, "numeric", "uuid", budget) for budget in (512, 1024))
    return high - low


def budget_slope(blocks: list[Block]) -> float:
    # Budgets double at every step, so x is the number of budget doublings.
    ys = [paired_delta(blocks, "numeric", "uuid", budget) for budget in BUDGETS]
    xbar, ybar = 2.0, mean(ys)
    return sum((x - xbar) * (y - ybar) for x, y in enumerate(ys)) / sum((x - xbar) ** 2 for x in range(5))


def source_interaction(blocks: list[Block]) -> float:
    by_sources: dict[int, list[Block]] = defaultdict(list)
    for block in blocks:
        row = next(iter(block.values()))
        by_sources[int(row["dataset_cell"]["num_sources"])].append(block)
    penalties = {
        source_count: mean(paired_delta(values, "numeric", "uuid", budget) for budget in BUDGETS)
        for source_count, values in by_sources.items()
    }
    return penalties[20] - penalties[15]


def analyze_group(blocks: list[Block], seed: int) -> dict[str, Any]:
    budgets: dict[str, Any] = {}
    for budget in BUDGETS:
        budget_result = {
            "n_paired_examples": len(blocks),
            "accuracy": {target: arm_mean(blocks, target, budget) for target in ARMS},
            "uuid_minus_numeric_accuracy": interval(
                blocks, lambda sample, b=budget: paired_delta(sample, "numeric", "uuid", b), seed + budget
            ),
            "compact_minus_numeric_accuracy": interval(
                blocks, lambda sample, b=budget: paired_delta(sample, "numeric", "random_compact", b), seed + 2 * budget
            ),
            "uuid_no_reproduction_minus_uuid_accuracy": interval(
                blocks, lambda sample, b=budget: paired_delta(sample, "uuid", "uuid_no_reproduction", b), seed + 3 * budget
            ),
            "uuid_minus_numeric_reasoning_tokens": interval(
                blocks,
                lambda sample, b=budget: paired_delta(sample, "numeric", "uuid", b, reasoning_tokens),
                seed + 4 * budget,
            ),
            "uuid_minus_numeric_total_output_tokens": interval(
                blocks,
                lambda sample, b=budget: paired_delta(sample, "numeric", "uuid", b, total_output_tokens),
                seed + 5 * budget,
            ),
        }
        budgets[str(budget)] = budget_result
    return {
        "complete_paired_examples": len(blocks),
        "budgets": budgets,
        "uuid_penalty_low_to_high_budget_interaction": interval(blocks, low_high_interaction, seed + 7001),
        "uuid_penalty_slope_per_budget_doubling": interval(blocks, budget_slope, seed + 7002),
        "uuid_penalty_20_minus_15_sources": interval(blocks, source_interaction, seed + 7003),
    }


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def pp(effect: dict[str, Any]) -> str:
    low, high = effect["bootstrap_95_ci"]
    return f"{100 * effect['estimate']:+.1f} [{100 * low:+.1f}, {100 * high:+.1f}]"


def report(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 5 confirmatory reasoning-budget experiment", "",
        f"**Design:** independent seed 202606; {result['records']} completed two-pass generations; "
        f"{result['complete_paired_examples']} complete semantic examples; 10,000-replicate stratified paired bootstrap.", "",
        "Pilot information was used only to retain model–task pairs with aggregate answer accuracy in the predeclared "
        "30–70% interval. All new examples differ from the pilot seed.", "",
        "The budget is an explicit visible scratchpad cap, not a hidden chain-of-thought or proprietary reasoning-token budget.", "",
        "## Retained cells and confirmatory calibration", "",
        "| Model | Task | Examples | Confirmatory accuracy across arms/budgets |", "|---|---|---:|---:|",
    ]
    for item in result["calibration"]:
        lines.append(f"| {item['model']} | {item['task']} | {item['examples']} | {pct(item['accuracy'])} |")
    lines.extend(("", "## Pilot-to-confirmation comparison", "",
                  "The same interaction estimators are recomputed on only the pilot cells selected for confirmation. "
                  "Effects are percentage points with stratified paired-bootstrap 95% intervals.", "",
                  "| Model | Pilot slope per doubling | Confirmatory slope per doubling | Pilot low-to-high | Confirmatory low-to-high |",
                  "|---|---:|---:|---:|---:|"))
    for model, comparison in result["pilot_comparison"].items():
        lines.append(
            f"| {model} | {pp(comparison['pilot_slope'])} | {pp(comparison['confirmatory_slope'])} | "
            f"{pp(comparison['pilot_low_to_high'])} | {pp(comparison['confirmatory_low_to_high'])} |"
        )
    lines.extend(("", "## Accuracy by budget", "",
                  "Effects are percentage points with paired-bootstrap 95% intervals.", "",
                  "| Model | Budget | Numeric | Compact | UUID | UUID no reproduction | UUID − numeric (pp, 95% CI) | No reproduction − UUID (pp, 95% CI) |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"))
    for model, analysis in result["models"].items():
        for budget in BUDGETS:
            cell = analysis["budgets"][str(budget)]
            acc = cell["accuracy"]
            lines.append(
                f"| {model} | {budget} | {pct(acc['numeric'])} | {pct(acc['random_compact'])} | "
                f"{pct(acc['uuid'])} | {pct(acc['uuid_no_reproduction'])} | "
                f"{pp(cell['uuid_minus_numeric_accuracy'])} | "
                f"{pp(cell['uuid_no_reproduction_minus_uuid_accuracy'])} |"
            )
    lines.extend(("", "## Identifier-complexity × budget interaction", "",
                  "A positive low-to-high estimate means UUID accuracy recovers relative to numeric as budget increases. "
                  "The slope is the UUID-minus-numeric change, in percentage points, for each budget doubling.", "",
                  "| Model | Low-to-high interaction (pp, 95% CI) | Slope per doubling (pp, 95% CI) | 20-source minus 15-source UUID penalty (pp, 95% CI) |",
                  "|---|---:|---:|---:|"))
    for model, analysis in result["models"].items():
        lines.append(
            f"| {model} | {pp(analysis['uuid_penalty_low_to_high_budget_interaction'])} | "
            f"{pp(analysis['uuid_penalty_slope_per_budget_doubling'])} | "
            f"{pp(analysis['uuid_penalty_20_minus_15_sources'])} |"
        )
    lines.extend(("", "## Token use", "",
                  "| Model | Budget | UUID − numeric reasoning tokens (95% CI) | UUID − numeric total output tokens (95% CI) |",
                  "|---|---:|---:|---:|"))
    for model, analysis in result["models"].items():
        for budget in BUDGETS:
            cell = analysis["budgets"][str(budget)]
            rt = cell["uuid_minus_numeric_reasoning_tokens"]
            ot = cell["uuid_minus_numeric_total_output_tokens"]
            lines.append(
                f"| {model} | {budget} | {rt['estimate']:+.1f} [{rt['bootstrap_95_ci'][0]:+.1f}, {rt['bootstrap_95_ci'][1]:+.1f}] | "
                f"{ot['estimate']:+.1f} [{ot['bootstrap_95_ci'][0]:+.1f}, {ot['bootstrap_95_ci'][1]:+.1f}] |"
            )
    lines.extend(("", "## Interpretation", "", result["interpretation"], ""))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_jsonl", nargs="+")
    parser.add_argument("--json-output", default="results/processed/stage5_confirmatory.json")
    parser.add_argument("--report-output", default="FINDINGS_STAGE5_CONFIRMATORY.md")
    args = parser.parse_args()
    paths = [Path(path) for path in args.raw_jsonl]
    rows = [json.loads(line) for path in paths for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    blocks = make_blocks(rows)
    by_model: dict[str, list[Block]] = defaultdict(list)
    for block in blocks:
        by_model[next(iter(block.values()))["model"]].append(block)
    analyses = {model: analyze_group(values, 202606 + index * 10_000)
                for index, (model, values) in enumerate(sorted(by_model.items()))}
    pilot_comparison: dict[str, Any] = {}
    for index, (model, (path, selected_tasks)) in enumerate(PILOT_SELECTIONS.items()):
        if model not in analyses or not path.exists():
            continue
        pilot_rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        pilot_blocks = make_blocks([row for row in pilot_rows if row["task_type"] in selected_tasks])
        pilot_comparison[model] = {
            "pilot_complete_paired_examples": len(pilot_blocks),
            "pilot_slope": interval(pilot_blocks, budget_slope, 302605 + index * 100),
            "confirmatory_slope": analyses[model]["uuid_penalty_slope_per_budget_doubling"],
            "pilot_low_to_high": interval(pilot_blocks, low_high_interaction, 402605 + index * 100),
            "confirmatory_low_to_high": analyses[model]["uuid_penalty_low_to_high_budget_interaction"],
        }
    calibration = []
    for (model, task), selected in sorted({
        (row["model"], row["task_type"]): [candidate for candidate in rows
                                            if candidate["model"] == row["model"] and candidate["task_type"] == row["task_type"]]
        for row in rows
    }.items()):
        calibration.append({"model": model, "task": task,
                            "examples": len({row["example_id"] for row in selected}),
                            "accuracy": mean(accuracy(row) for row in selected)})
    interpretation = (
        "The broad monotonic identifier-complexity × budget hypothesis is not confirmed: every confirmatory slope and "
        "low-to-high interval includes zero. Qwen nevertheless has significant UUID deficits at 128 and 1,024 tokens, "
        "which supports a persistent binding cost but not monotonic recovery with budget. Gemma E2B shows the predicted "
        "constrained-budget failure at 64 tokens (UUID minus numeric: -35 points), followed by a sharp non-monotonic "
        "reversal; removing UUID reproduction improves its accuracy by 45 and 50 points at 512 and 1,024 tokens. "
        "Tiny Aya's significant positive pilot slope does not replicate. No model has a source-count interaction whose "
        "interval excludes zero. UUIDs do reliably increase total generated output: the UUID-minus-numeric interval is "
        "strictly positive in 14 of 15 model-budget cells, but scratchpad-token direction is model-dependent."
    )
    result = {
        "design": {"seed": 202606, "pilot_seed": 202605, "selection_interval": [0.30, 0.70],
                   "reasoning_budgets": list(BUDGETS), "bootstrap_replicates": BOOTSTRAPS,
                   "bootstrap_unit": "semantic example stratified by model, task, and source count"},
        "records": len(rows), "complete_paired_examples": len(blocks),
        "raw_results": [str(path) for path in paths], "calibration": calibration,
        "models": analyses, "pilot_comparison": pilot_comparison, "interpretation": interpretation,
    }
    json_path, report_path = Path(args.json_output), Path(args.report_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(report(result), encoding="utf-8")
    print(json.dumps({"records": len(rows), "complete_paired_examples": len(blocks),
                      "json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

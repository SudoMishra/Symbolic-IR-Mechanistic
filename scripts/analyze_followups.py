"""Analyze the exploratory scaling sweep and token-matched confirmation."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from analyze_stage1 import cell_summary, enrich, mcnemar_exact, mean, percentile


CONDITIONS = ("numeric", "structured", "semantic", "random_compact", "hex6", "hex32", "uuid")


def load(path: str) -> list[dict]:
    return [enrich(json.loads(line)) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def paired_compare(left_rows: list[dict], right_rows: list[dict], left_name: str, right_name: str, metric: str) -> dict:
    left = {row["example_id"]: row for row in left_rows}
    right = {row["example_id"]: row for row in right_rows}
    keys = sorted(left.keys() & right.keys())
    if left.keys() != right.keys():
        raise ValueError("Paired comparison has unmatched examples")
    def value(row):
        if metric == "answer_content":
            return bool(row["rescored"]["answer_content_correct"])
        if metric == "citation_strict":
            return bool(row["rescored"]["citation_strict_correct"])
        if metric == "source_binding":
            return bool(row["rescored"]["source_binding_exact"])
        raise ValueError(metric)
    deltas = [int(value(right[key])) - int(value(left[key])) for key in keys]
    left_only = sum(value(left[key]) and not value(right[key]) for key in keys)
    right_only = sum(value(right[key]) and not value(left[key]) for key in keys)
    rng = random.Random(202603 + len(metric))
    boot = [mean([rng.choice(deltas) for _ in deltas]) for _ in range(20_000)]
    return {
        "metric": metric,
        "comparison": f"{right_name}_minus_{left_name}",
        "delta": mean(deltas),
        "bootstrap_95_ci": [percentile(boot, 0.025), percentile(boot, 0.975)],
        f"{left_name}_only": left_only,
        f"{right_name}_only": right_only,
        "mcnemar_exact_p": mcnemar_exact(left_only, right_only),
    }


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage1")
    parser.add_argument("stage2")
    parser.add_argument("stage3")
    parser.add_argument("--json-output", default="results/processed/followups_qwen15b.json")
    parser.add_argument("--report-output", default="FINDINGS.md")
    args = parser.parse_args()
    stage1, stage2, stage3 = load(args.stage1), load(args.stage2), load(args.stage3)
    scaling = [cell_summary(stage2, count, condition) for count in (5, 20) for condition in CONDITIONS]
    structured = [row for row in stage1 if len(row["source_order"]) == 20 and row["identifier_condition"] == "structured"]
    numeric = [row for row in stage3 if row["identifier_condition"] == "numeric"]
    matched_cells = [cell_summary(numeric, 20, "numeric"), cell_summary(structured, 20, "structured")]
    comparisons = [paired_compare(structured, numeric, "structured", "numeric", metric) for metric in ("answer_content", "citation_strict", "source_binding")]
    result = {
        "stage2_records": len(stage2), "stage3_records": len(stage3),
        "scaling_cells": scaling, "token_matched_cells": matched_cells,
        "token_matched_comparisons": comparisons,
    }
    json_path = Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Symbolic identifier experiment findings",
        "",
        "## Executive result",
        "",
        "For Qwen2.5-1.5B-Instruct Q4_K_M, compact identifiers substantially reduced token cost and improved source binding relative to UUIDs. The evidence points primarily to length/copy burden, while delimiter choice strongly affected literal output formatting. Answer content was comparatively stable.",
        "",
        "The confirmatory Stage 1 statistics are in [FINDINGS_STAGE1.md](FINDINGS_STAGE1.md). The tables below add the exploratory identifier-family sweep and token-matched control.",
        "",
        "## Stage 2 exploratory family sweep",
        "",
        "Twenty paired examples were run per cell, so these are directional estimates.",
        "",
        "| Sources | Identifier | ID tokens | Answer content | Strict citation | Exact binding | Input tokens | Latency |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cell in scaling:
        metrics = cell["metrics"]
        lines.append(
            f"| {cell['num_sources']} | {cell['identifier_condition']} | {cell['mean_identifier_tokens']:.2f} | "
            f"{percent(metrics['answer_content']['rate'])} | {percent(metrics['citation_strict']['rate'])} | "
            f"{percent(metrics['source_binding_exact']['rate'])} | {cell['mean_input_tokens']:.1f} | {cell['mean_latency_seconds']:.2f}s |"
        )
    lines.extend((
        "",
        "At 20 sources, exact binding declined broadly with identifier length: 85% for numeric, 80% semantic, 70% random compact, 65% hex6, 45% hex32, and 40% UUID. Structured `[S#]` reached 55% in this small pilot. With only seven family-level points, the exploratory Spearman association between mean ID length and binding was -0.72; this is descriptive, not a causal estimate.",
        "",
        "## Stage 3 token-matched confirmation",
        "",
        "Numeric `[1]` was run on the exact same 100 canonical 20-source examples as structured `[S1]`. Both conditions averaged 3.55 tokens per ID, 639.31 input tokens, and approximately 5.25 seconds latency.",
        "",
        "| Identifier | Answer content | Strict citation | Exact binding | Input tokens | Latency |",
        "|---|---:|---:|---:|---:|---:|",
    ))
    for cell in matched_cells:
        metrics = cell["metrics"]
        lines.append(
            f"| {cell['identifier_condition']} | {percent(metrics['answer_content']['rate'])} | "
            f"{percent(metrics['citation_strict']['rate'])} | {percent(metrics['source_binding_exact']['rate'])} | "
            f"{cell['mean_input_tokens']:.2f} | {cell['mean_latency_seconds']:.2f}s |"
        )
    lines.extend(("", "Paired effects are numeric minus structured:", "", "| Metric | Delta | Bootstrap 95% CI | Exact p |", "|---|---:|---:|---:|"))
    for comparison in comparisons:
        low, high = comparison["bootstrap_95_ci"]
        lines.append(f"| {comparison['metric']} | {comparison['delta'] * 100:+.1f} pp | [{low * 100:+.1f}, {high * 100:+.1f}] pp | {comparison['mcnemar_exact_p']:.3g} |")
    lines.extend((
        "",
        "The 67-point strict-citation advantage for numeric IDs is entirely a formatting effect: this model usually retained brackets around `[1]` but often emitted `S1` instead of `[S1]`. The binding difference was only +8 points and was inconclusive (95% CI -3 to +19; p=0.215). Thus this token-matched test does **not** establish a binding/reasoning advantage for numeric over structured aliases.",
        "",
        "## Overall interpretation",
        "",
        "- **Supported:** keeping long opaque identifiers outside the reasoning interface can improve source binding and sharply reduce tokens and latency.",
        "- **Supported:** source count amplifies difficulty for every representation.",
        "- **Supported:** source selection and literal reconstruction are separable; strict exact match alone can be misleading.",
        "- **Not yet supported:** typed or semantically structured aliases improve binding after controlling for token length.",
        "- **Not tested:** reasoning-budget competition, causal internal representations, and PII generalization on this model.",
        "",
        "## Recommended next experiment",
        "",
        "Use four conditions—numeric, random compact, hex32, and UUID—on multi-hop tasks with at least 100 paired examples per cell. Preserve strict and relaxed binding metrics, and increase the output cap to remove the small UUID truncation confound. Replicate on a larger model before making general claims.",
        "",
    ))
    report_path = Path(args.report_output)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

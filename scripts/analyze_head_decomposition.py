#!/usr/bin/env python3
"""Phase 4 Head Attribution Analysis & Ranking Script.

Computes paired cluster-bootstrap 95% confidence intervals (B=1,000, clustered by example_id)
for each attention head, ranks heads by mean causal shift, evaluates specificity (KL divergence),
and extracts candidate head sets for confirmatory validation.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.analyze_circuit_results import cluster_bootstrap_mean_ci  # noqa: E402


def analyze_head_decomposition(
    input_file: Path,
    output_json: Path,
    output_md: Path | None = None,
    candidate_k_grid: list[int] = [1, 2, 3, 4],
) -> dict[str, Any]:
    lines = [json.loads(line) for line in input_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"No records found in {input_file}")

    print(f"\nAnalyzing head decomposition results from {input_file.name} ({len(lines)} cases)...")
    sample_row = lines[0]
    layer_1based = sample_row.get("layer_1based", sample_row.get("layer", 24))
    layer_0based = sample_row.get("layer_0based", layer_1based - 1)
    sem_pos = sample_row.get("semantic_position", "pos_citation")
    head_results_0 = sample_row["head_results"]
    num_heads = len(head_results_0)

    # Collect paired shifts: head -> list of (example_id, shift)
    head_shifts = defaultdict(list)
    head_recovs = defaultdict(list)
    head_kls = defaultdict(list)
    head_shifts_by_cond = defaultdict(lambda: defaultdict(list))

    clean_prefs = []
    donor_prefs = []

    for row in lines:
        ex_id = row["example_id"]
        cond = row["condition"]
        c_pref = row["clean_baseline"]["first_token_pref"]
        d_pref = row["donor_baseline"]["first_token_pref"]
        clean_prefs.append((ex_id, c_pref))
        donor_prefs.append((ex_id, d_pref))

        for h_str, h_res in row["head_results"].items():
            h = int(h_str)
            shift = h_res["abs_shift_first"]
            kl = h_res.get("kl_div", 0.0)
            recov = h_res.get("recovery_pct")

            head_shifts[h].append((ex_id, shift))
            head_kls[h].append((ex_id, kl))
            head_shifts_by_cond[cond][h].append((ex_id, shift))
            if recov is not None:
                head_recovs[h].append((ex_id, recov))

    # Compute cluster bootstrap statistics for each head
    ranked_heads = []
    for h in range(num_heads):
        s_mean, s_low, s_high = cluster_bootstrap_mean_ci(head_shifts[h], n_boot=1000)
        kl_mean, kl_low, kl_high = cluster_bootstrap_mean_ci(head_kls[h], n_boot=1000) if head_kls[h] else (0.0, 0.0, 0.0)
        r_mean, r_low, r_high = cluster_bootstrap_mean_ci(head_recovs[h], n_boot=1000) if head_recovs[h] else (0.0, 0.0, 0.0)

        # Condition-specific breakdowns
        cond_breakdown = {}
        for cond, cond_heads in head_shifts_by_cond.items():
            if h in cond_heads:
                cs_mean, cs_low, cs_high = cluster_bootstrap_mean_ci(cond_heads[h], n_boot=1000)
                cond_breakdown[cond] = {
                    "mean_shift": round(float(cs_mean), 4),
                    "shift_ci_95": [round(float(cs_low), 4), round(float(cs_high), 4)],
                    "n_cases": len(cond_heads[h]),
                }

        is_stat_positive = bool(s_low > 0)
        ranked_heads.append({
            "head": h,
            "layer_1based": layer_1based,
            "layer_0based": layer_0based,
            "semantic_position": sem_pos,
            "mean_shift": round(float(s_mean), 4),
            "shift_ci_95": [round(float(s_low), 4), round(float(s_high), 4)],
            "mean_recovery_pct": round(float(r_mean), 2),
            "recovery_ci_95": [round(float(r_low), 2), round(float(r_high), 2)],
            "mean_kl_div": round(float(kl_mean), 4),
            "kl_ci_95": [round(float(kl_low), 4), round(float(kl_high), 4)],
            "ci_excludes_zero": is_stat_positive,
            "condition_breakdown": cond_breakdown,
        })

    # Sort strictly by mean causal shift descending
    ranked_heads.sort(key=lambda x: x["mean_shift"], reverse=True)
    for rank_idx, item in enumerate(ranked_heads, start=1):
        item["rank"] = rank_idx

    # Candidate head selection for allowed K grid
    candidate_subsets = {}
    for k in candidate_k_grid:
        if k <= len(ranked_heads):
            top_k_heads = [item["head"] for item in ranked_heads[:k]]
            candidate_subsets[f"top_{k}"] = {
                "k": k,
                "heads": top_k_heads,
                "sum_individual_shifts": round(sum(item["mean_shift"] for item in ranked_heads[:k]), 4),
                "all_ci_exclude_zero": all(item["ci_excludes_zero"] for item in ranked_heads[:k]),
            }

    c_base_mean, c_low, c_high = cluster_bootstrap_mean_ci(clean_prefs, n_boot=1000)
    d_base_mean, d_low, d_high = cluster_bootstrap_mean_ci(donor_prefs, n_boot=1000)

    synthesis = {
        "title": f"Sequence 3A: Attention Head Causal Screening (Layer L{layer_1based}, {sem_pos})",
        "total_cases": len(lines),
        "layer_1based": layer_1based,
        "layer_0based": layer_0based,
        "semantic_position": sem_pos,
        "clean_baseline_pref": {"mean": round(float(c_base_mean), 4), "ci_95": [round(float(c_low), 4), round(float(c_high), 4)]},
        "donor_baseline_pref": {"mean": round(float(d_base_mean), 4), "ci_95": [round(float(d_low), 4), round(float(d_high), 4)]},
        "ranked_heads": ranked_heads,
        "candidate_subsets": candidate_subsets,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(synthesis, indent=2), encoding="utf-8")
    print(f"Saved head synthesis JSON to: {output_json}")

    # Build Markdown Report
    if output_md:
        md_lines = [
            f"# Sequence 3A Head Causal Screening Report: Layer L{layer_1based} ({sem_pos})",
            "",
            "## Methodological Overview",
            f"- **Layer**: Scientific Layer L{layer_1based} (Stack index {layer_0based})",
            f"- **Position**: `{sem_pos}`",
            f"- **Total Evaluated Cases**: {len(lines)} cases from discovery split",
            "- **Statistical Rigor**: All confidence intervals computed using paired cluster bootstrap ($B=1,000$, clustered by `example_id`).",
            "",
            "## Ranked Attention Heads",
            "",
            "| Rank | Head | Mean Causal Shift $\\Delta_{\\text{First}}$ | 95% CI | Recovery % | 95% CI | KL Div | $L_{\\text{CI}} > 0$ |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for r in ranked_heads:
            ci_str = f"[{r['shift_ci_95'][0]:+.3f}, {r['shift_ci_95'][1]:+.3f}]"
            r_ci_str = f"[{r['recovery_ci_95'][0]:+.1f}%, {r['recovery_ci_95'][1]:+.1f}%]"
            star = "YES" if r["ci_excludes_zero"] else "NO"
            md_lines.append(
                f"| {r['rank']} | L{layer_1based}H{r['head']} | {r['mean_shift']:+.3f} nats | {ci_str} | {r['mean_recovery_pct']:+.1f}% | {r_ci_str} | {r['mean_kl_div']:.4f} | {star} |"
            )

        md_lines.extend([
            "",
            "## Candidate Head Subsets for Validation",
            "",
        ])
        for k_key, sub in candidate_subsets.items():
            head_labels = ", ".join(f"L{layer_1based}H{h}" for h in sub["heads"])
            md_lines.append(f"- **{k_key.upper()} (K={sub['k']})**: [{head_labels}] (Sum individual shifts: {sub['sum_individual_shifts']:+.3f} nats, all $L_{{\\text{{CI}}}} > 0$: {sub['all_ci_exclude_zero']})")

        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text("\n".join(md_lines), encoding="utf-8")
        print(f"Saved head synthesis markdown to: {output_md}")

    return synthesis


def main():
    parser = argparse.ArgumentParser(description="Analyze Sequence 3A Head Decomposition")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--output_md", default=None)
    parser.add_argument("--k_grid", nargs="+", type=int, default=[1, 2, 3, 4])
    args = parser.parse_args()

    analyze_head_decomposition(
        input_file=Path(args.input),
        output_json=Path(args.output_json),
        output_md=Path(args.output_md) if args.output_md else None,
        candidate_k_grid=args.k_grid,
    )


if __name__ == "__main__":
    main()

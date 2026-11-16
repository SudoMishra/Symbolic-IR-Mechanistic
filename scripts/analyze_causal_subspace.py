#!/usr/bin/env python3
"""Phase 5: Statistical Analysis of Causal Subspace Evaluation.

Aggregates causal projection shifts, recovery percentages, and control baselines
across subspace ranks k in {1, 2, 4, 8, 16, 32} with paired cluster bootstrap (B=1,000).
Selects optimal rank k* according to preregistered rule:
  min k such that recovery >= 70% and margin_over_random >= 30%.
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


def bootstrapped_ratio_ci(
    numer_pairs: list[tuple[str, float]],
    denom_pairs: list[tuple[str, float]],
    b_reps: int = 1000,
    seed: int = 202671,
) -> tuple[float, float, float]:
    """Compute jointly bootstrapped ratio of aggregate means clustered by example_id."""
    assert len(numer_pairs) == len(denom_pairs)
    rng = np.random.default_rng(seed)

    # Group by cluster unit (example_id)
    clusters = defaultdict(list)
    for (cid, n_val), (_, d_val) in zip(numer_pairs, denom_pairs):
        clusters[cid].append((n_val, d_val))

    unique_ids = list(clusters.keys())
    m = len(unique_ids)

    # Point estimate: aggregate mean ratio
    sum_num = sum(n for _, n in numer_pairs)
    sum_den = sum(d for _, d in denom_pairs)
    pt_est = (sum_num / sum_den * 100.0) if abs(sum_den) > 1e-6 else 0.0

    boot_ratios = []
    for _ in range(b_reps):
        sampled_cids = rng.choice(unique_ids, size=m, replace=True)
        b_num = 0.0
        b_den = 0.0
        for cid in sampled_cids:
            for n_val, d_val in clusters[cid]:
                b_num += n_val
                b_den += d_val
        if abs(b_den) > 1e-6:
            boot_ratios.append(b_num / b_den * 100.0)

    if boot_ratios:
        low = float(np.percentile(boot_ratios, 2.5))
        high = float(np.percentile(boot_ratios, 97.5))
    else:
        low, high = 0.0, 0.0

    return pt_est, low, high


def analyze_causal_subspace(
    eval_file: Path,
    output_json: Path,
    output_md: Path,
    basis_file: Path | None = None,
) -> dict[str, Any]:
    lines = [json.loads(line) for line in eval_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"No records found in {eval_file}")

    print(f"Analyzing {len(lines)} subspace evaluation records from {eval_file.name}...")

    # Discover evaluated ranks from first record
    ranks = sorted([int(k) for k in lines[0]["rank_evaluations"].keys()])

    # Accumulate by rank and condition
    shifts_by_rank = defaultdict(list)
    recovery_numer_by_rank = defaultdict(list)
    recovery_denom_by_rank = defaultdict(list)
    kl_by_rank = defaultdict(list)

    rand_shifts_by_rank = defaultdict(list)
    rand_numer_by_rank = defaultdict(list)

    comp_shifts_by_rank = defaultdict(list)
    comp_numer_by_rank = defaultdict(list)

    # By condition breakdown
    cond_shifts = defaultdict(lambda: defaultdict(list))
    cond_numer = defaultdict(lambda: defaultdict(list))
    cond_denom = defaultdict(lambda: defaultdict(list))

    denom_guard = 0.5

    for row in lines:
        cid = row["example_id"]
        cond = row["condition"]
        c_pref = row["clean_baseline_pref"]
        d_pref = row["donor_baseline_pref"]
        denom = d_pref - c_pref

        has_valid_denom = abs(denom) > denom_guard

        for k in ranks:
            k_str = str(k)
            # Subspace projection
            k_eval = row["rank_evaluations"][k_str]
            s_val = k_eval["abs_shift_first"]
            kl_val = k_eval.get("kl_div", 0.0)
            shifts_by_rank[k].append((cid, s_val))
            kl_by_rank[k].append((cid, kl_val))

            cond_shifts[cond][k].append((cid, s_val))

            if has_valid_denom:
                recovery_numer_by_rank[k].append((cid, s_val))
                recovery_denom_by_rank[k].append((cid, denom))
                cond_numer[cond][k].append((cid, s_val))
                cond_denom[cond][k].append((cid, denom))

            # Random control
            r_eval = row["random_control_evaluations"][k_str]
            r_shift = r_eval["abs_shift_first"]
            rand_shifts_by_rank[k].append((cid, r_shift))
            if has_valid_denom:
                rand_numer_by_rank[k].append((cid, r_shift))

            # Complement control
            c_eval = row["orthogonal_complement_evaluations"][k_str]
            c_shift = c_eval["abs_shift_first"]
            comp_shifts_by_rank[k].append((cid, c_shift))
            if has_valid_denom:
                comp_numer_by_rank[k].append((cid, c_shift))

    # Compile synthesis
    rank_summaries = {}
    optimal_rank = None
    min_recovery_threshold = 70.0
    min_margin_threshold = 30.0

    for k in ranks:
        s_mean, s_low, s_high = cluster_bootstrap_mean_ci(shifts_by_rank[k])
        kl_mean, kl_low, kl_high = cluster_bootstrap_mean_ci(kl_by_rank[k])
        r_mean, r_low, r_high = cluster_bootstrap_mean_ci(rand_shifts_by_rank[k])
        c_mean, c_low, c_high = cluster_bootstrap_mean_ci(comp_shifts_by_rank[k])

        rec_pt, rec_low, rec_high = bootstrapped_ratio_ci(
            recovery_numer_by_rank[k], recovery_denom_by_rank[k]
        )
        rand_rec_pt, rand_rec_low, rand_rec_high = bootstrapped_ratio_ci(
            rand_numer_by_rank[k], recovery_denom_by_rank[k]
        )
        comp_rec_pt, comp_rec_low, comp_rec_high = bootstrapped_ratio_ci(
            comp_numer_by_rank[k], recovery_denom_by_rank[k]
        )

        margin_over_random = rec_pt - rand_rec_pt
        qualifies = (rec_pt >= min_recovery_threshold) and (margin_over_random >= min_margin_threshold)

        if qualifies and optimal_rank is None:
            optimal_rank = k

        rank_summaries[str(k)] = {
            "rank": k,
            "shift_mean": s_mean,
            "shift_ci_95": [s_low, s_high],
            "recovery_pct": rec_pt,
            "recovery_ci_95": [rec_low, rec_high],
            "random_shift_mean": r_mean,
            "random_recovery_pct": rand_rec_pt,
            "margin_over_random_pct": margin_over_random,
            "complement_shift_mean": c_mean,
            "complement_recovery_pct": comp_rec_pt,
            "kl_div": kl_mean,
            "kl_ci_95": [kl_low, kl_high],
            "qualifies_preregistered_rule": qualifies,
        }

    # Format condition breakdown
    condition_summaries = {}
    for cond in cond_shifts.keys():
        cond_data = {}
        for k in ranks:
            c_s_mean, c_s_low, c_s_high = cluster_bootstrap_mean_ci(cond_shifts[cond][k])
            c_rec_pt, c_rec_low, c_rec_high = bootstrapped_ratio_ci(
                cond_numer[cond][k], cond_denom[cond][k]
            )
            cond_data[str(k)] = {
                "shift_mean": c_s_mean,
                "shift_ci_95": [c_s_low, c_s_high],
                "recovery_pct": c_rec_pt,
                "recovery_ci_95": [c_rec_low, c_rec_high],
            }
        condition_summaries[cond] = cond_data

    # Fallback if no rank strictly meets both thresholds
    if optimal_rank is None:
        # Choose rank with highest margin over random
        best_k = max(ranks, key=lambda k: rank_summaries[str(k)]["margin_over_random_pct"])
        optimal_rank = best_k
        selection_note = f"Fallback to rank with highest margin over random ({best_k})"
    else:
        selection_note = f"Smallest rank meeting >= {min_recovery_threshold}% recovery and >= {min_margin_threshold}% margin over random"

    synthesis = {
        "title": "Phase 5: Post-Evidence Residual Causal Subspace Evaluation",
        "eval_dataset": eval_file.name,
        "total_cases": len(lines),
        "target_layer_1based": lines[0]["layer_1based"],
        "semantic_position": lines[0]["semantic_position"],
        "optimal_rank": optimal_rank,
        "selection_rule_status": selection_note,
        "rank_summaries": rank_summaries,
        "condition_summaries": condition_summaries,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(synthesis, indent=2), encoding="utf-8")
    print(f"Saved subspace synthesis JSON to: {output_json}")

    # Build Markdown table
    md_lines = [
        "# Phase 5: Post-Evidence Causal Subspace Evaluation",
        "",
        f"- **Dataset**: `{eval_file.name}` ({len(lines)} cases)",
        f"- **Target**: Layer {lines[0]['layer_1based']} (`pos_post_evidence` residual stream)",
        f"- **Optimal Selected Rank**: **k* = {optimal_rank}** ({selection_note})",
        "",
        "| Rank $k$ | Causal Shift [95% CI] | Recovery % [95% CI] | Random Control Recovery % | Margin over Random | Complement Recovery % | KL Div | Qualifies |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for k in ranks:
        r = rank_summaries[str(k)]
        s_str = f"{r['shift_mean']:+.4f} [{r['shift_ci_95'][0]:.4f}, {r['shift_ci_95'][1]:.4f}]"
        rec_str = f"{r['recovery_pct']:.1f}% [{r['recovery_ci_95'][0]:.1f}%, {r['recovery_ci_95'][1]:.1f}%]"
        rand_str = f"{r['random_recovery_pct']:.1f}%"
        margin_str = f"{r['margin_over_random_pct']:+.1f}%"
        comp_str = f"{r['complement_recovery_pct']:.1f}%"
        kl_str = f"{r['kl_div']:.3f}"
        q_str = "**YES**" if r["qualifies_preregistered_rule"] else "No"
        md_lines.append(f"| {k} | {s_str} | {rec_str} | {rand_str} | {margin_str} | {comp_str} | {kl_str} | {q_str} |")

    md_lines.extend([
        "",
        "### Condition-Specific Transfer Matrix",
        "",
        "| Condition | Rank 1 Recovery | Rank 4 Recovery | Rank 8 Recovery | Rank 16 Recovery | Rank 32 Recovery |",
        "|---|---|---|---|---|---|",
    ])

    for cond, cdata in condition_summaries.items():
        r1 = f"{cdata.get('1', {}).get('recovery_pct', 0.0):.1f}%"
        r4 = f"{cdata.get('4', {}).get('recovery_pct', 0.0):.1f}%"
        r8 = f"{cdata.get('8', {}).get('recovery_pct', 0.0):.1f}%"
        r16 = f"{cdata.get('16', {}).get('recovery_pct', 0.0):.1f}%"
        r32 = f"{cdata.get('32', {}).get('recovery_pct', 0.0):.1f}%"
        md_lines.append(f"| `{cond}` | {r1} | {r4} | {r8} | {r16} | {r32} |")

    output_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Saved subspace findings Markdown to: {output_md}")
    return synthesis


def main():
    parser = argparse.ArgumentParser(description="Phase 5: Analyze Causal Subspace Results")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    analyze_causal_subspace(
        eval_file=Path(args.input),
        output_json=Path(args.output_json),
        output_md=Path(args.output_md),
    )


if __name__ == "__main__":
    main()

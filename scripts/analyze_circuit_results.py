#!/usr/bin/env python3
"""Statistical analysis and dissociation metrics for circuit decomposition results.

Features:
1. Cluster-robust bootstrap grouped by example_id (respects semantic sample size).
2. Primary reporting of raw effect shifts (Mixer vs MLP) alongside baseline swap shift.
3. Candidate own-prefix continuation preference (clean vs swapped) and recovery.
4. Specificity controls: Post-citation syntax preservation and vocabulary KL divergence (in nats).
5. Dissociation Index and condition-stratified breakdowns.
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
sys.path.insert(0, str(ROOT / "src"))


def cluster_bootstrap_mean_ci(
    items: list[tuple[str, float]],
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 202611,
) -> tuple[float, float, float]:
    """Cluster-robust bootstrap mean and 95% confidence interval grouped by cluster_id.

    Resamples entire example clusters with replacement to preserve within-cluster covariance.
    """
    valid_items = [(cid, v) for cid, v in items if v is not None and not math.isnan(v)]
    if not valid_items:
        return 0.0, 0.0, 0.0

    all_vals = [v for _, v in valid_items]
    mean_val = float(np.mean(all_vals))

    # Group by cluster ID (example_id)
    clusters = defaultdict(list)
    for cid, v in valid_items:
        clusters[cid].append(v)

    cluster_keys = list(clusters.keys())
    if len(cluster_keys) < 3:
        return round(mean_val, 4), round(mean_val, 4), round(mean_val, 4)

    cluster_vals = [np.array(clusters[k], dtype=np.float64) for k in cluster_keys]
    num_clusters = len(cluster_vals)

    rng = np.random.default_rng(seed)
    boot_means = []
    for _ in range(n_boot):
        sample_indices = rng.choice(num_clusters, size=num_clusters, replace=True)
        sampled_vals = [v for idx in sample_indices for v in cluster_vals[idx]]
        boot_means.append(float(np.mean(sampled_vals)))

    low = float(np.percentile(boot_means, 100 * (alpha / 2)))
    high = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    return round(mean_val, 4), round(low, 4), round(high, 4)


def analyze_decomposition(input_file: Path, output_file: Path):
    lines = [json.loads(line) for line in input_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        print(f"No records found in {input_file}")
        return

    unique_examples = sorted(set(r["example_id"] for r in lines))
    print(f"\nAnalyzing {len(lines)} cases ({len(unique_examples)} unique example clusters) from {input_file.name}...")

    layers = list(lines[0]["layer_results"].keys())
    interventions = ["mixer", "mlp", "both"]

    # Overall: layer -> intervention -> metric -> list of (example_id, value)
    aggregated = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    # By condition: cond -> layer -> intervention -> metric -> list of (example_id, value)
    by_condition = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    # Baseline shifts: overall and by condition
    base_shifts = defaultdict(list)
    base_shifts_by_cond = defaultdict(lambda: defaultdict(list))

    for row in lines:
        cid = row["example_id"]
        cond = row["condition"]

        b_first = row.get("base_shift_first")
        b_cont = row.get("base_shift_cont")

        if b_first is not None:
            base_shifts["first"].append((cid, b_first))
            base_shifts_by_cond[cond]["first"].append((cid, b_first))
        if b_cont is not None:
            base_shifts["cont"].append((cid, b_cont))
            base_shifts_by_cond[cond]["cont"].append((cid, b_cont))

        for layer_str, int_map in row["layer_results"].items():
            for int_type in interventions:
                m = int_map[int_type]
                for k in [
                    "abs_shift_first",
                    "abs_shift_cont",
                    "first_token_pref",
                    "cont_pref",
                    "recovery_first_pct",
                    "recovery_cont_pct",
                    "syntax_shift",
                    "kl_div",
                ]:
                    val = m.get(k)
                    if val is not None:
                        aggregated[layer_str][int_type][k].append((cid, val))
                        by_condition[cond][layer_str][int_type][k].append((cid, val))

    # Baseline summary
    base_summary = {
        "first": cluster_bootstrap_mean_ci(base_shifts["first"]),
        "cont": cluster_bootstrap_mean_ci(base_shifts["cont"]) if base_shifts["cont"] else None,
        "by_condition": {},
    }
    for cond, cd in base_shifts_by_cond.items():
        base_summary["by_condition"][cond] = {
            "first": cluster_bootstrap_mean_ci(cd["first"]),
            "cont": cluster_bootstrap_mean_ci(cd["cont"]) if cd["cont"] else None,
        }

    # Layer summaries
    summary = {
        "total_cases": len(lines),
        "unique_examples": len(unique_examples),
        "baseline_swap_shifts": base_summary,
        "layers": {},
        "by_condition": {},
    }

    def summarize_layer_dict(agg_dict):
        layer_summary = {}
        for layer_str in sorted(layers, key=lambda x: int(x)):
            layer_data = {}
            for int_type in interventions:
                int_data = {}
                for metric, tuples in agg_dict[layer_str][int_type].items():
                    mean_v, low, high = cluster_bootstrap_mean_ci(tuples)
                    int_data[metric] = {"mean": mean_v, "ci_95": [low, high]}
                layer_data[int_type] = int_data

            # Compute Dissociation Index if continuation available
            mix_first = layer_data["mixer"].get("abs_shift_first", {}).get("mean", 0.0)
            mlp_first = layer_data["mlp"].get("abs_shift_first", {}).get("mean", 0.0)
            joint_first = layer_data["both"].get("abs_shift_first", {}).get("mean", 0.0)

            mix_cont_dict = layer_data["mixer"].get("abs_shift_cont")
            mlp_cont_dict = layer_data["mlp"].get("abs_shift_cont")
            joint_cont_dict = layer_data["both"].get("abs_shift_cont")

            if mix_cont_dict and mlp_cont_dict and joint_cont_dict:
                mix_cont = mix_cont_dict["mean"]
                mlp_cont = mlp_cont_dict["mean"]
                joint_cont = joint_cont_dict["mean"]
                first_diff = (mix_first - mlp_first) / abs(joint_first) if abs(joint_first) > 0.1 else 0.0
                cont_diff = (mix_cont - mlp_cont) / abs(joint_cont) if abs(joint_cont) > 0.1 else 0.0
                layer_data["dissociation_index"] = round(first_diff - cont_diff, 4)
            else:
                layer_data["dissociation_index"] = None

            layer_summary[layer_str] = layer_data
        return layer_summary

    summary["layers"] = summarize_layer_dict(aggregated)
    for cond in sorted(by_condition.keys()):
        summary["by_condition"][cond] = summarize_layer_dict(by_condition[cond])

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved analysis to {output_file}")

    # Print summary table
    b_first_m = base_summary["first"][0]
    b_cont_m = base_summary["cont"][0] if base_summary["cont"] else "N/A"
    print("\n" + "=" * 115)
    print(f"BASELINE DIRECT SWAP EFFECT: ΔFirst = {b_first_m:+.3f} [{base_summary['first'][1]:+.2f}, {base_summary['first'][2]:+.2f}] | ΔCont = {b_cont_m}")
    if b_first_m <= 0:
        print("  [NOTE] Negative direct first-token shift indicates baseline stale-binding preference on this cohort.")
    print("=" * 115)
    print(f"{'Layer':<6} | {'Comp':<6} | {'Abs Shift First (B)':<22} | {'Abs Shift Cont (F)':<22} | {'Recov First %':<14} | {'KL (nats)':<10} | {'ΔSyntax':<8}")
    print("-" * 115)
    for layer_str, d in summary["layers"].items():
        for comp in ["mixer", "mlp", "both"]:
            s_first = f"{d[comp]['abs_shift_first']['mean']:+.3f} [{d[comp]['abs_shift_first']['ci_95'][0]:+.2f}, {d[comp]['abs_shift_first']['ci_95'][1]:+.2f}]"
            if "abs_shift_cont" in d[comp]:
                s_cont = f"{d[comp]['abs_shift_cont']['mean']:+.3f} [{d[comp]['abs_shift_cont']['ci_95'][0]:+.2f}, {d[comp]['abs_shift_cont']['ci_95'][1]:+.2f}]"
            else:
                s_cont = "N/A"
            r_first = f"{d[comp]['recovery_first_pct']['mean']:.1f}%" if "recovery_first_pct" in d[comp] else "N/A"
            kl = f"{d[comp]['kl_div']['mean']:.4f}" if "kl_div" in d[comp] else "0.0000"
            syn = f"{d[comp]['syntax_shift']['mean']:+.3f}" if "syntax_shift" in d[comp] else "N/A"
            print(f"{layer_str:<6} | {comp:<6} | {s_first:<22} | {s_cont:<22} | {r_first:<14} | {kl:<10} | {syn:<8}")
        print("-" * 115)


def main():
    parser = argparse.ArgumentParser(description="Analyze circuit decomposition")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    analyze_decomposition(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()

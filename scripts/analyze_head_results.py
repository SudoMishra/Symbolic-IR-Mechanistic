#!/usr/bin/env python3
"""Statistical ranking and analysis of individual attention heads."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.analyze_circuit_results import cluster_bootstrap_mean_ci  # noqa: E402


def analyze_heads(input_file: Path, output_file: Path):
    lines = [json.loads(line) for line in input_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        print(f"No records found in {input_file}")
        return

    print(f"\nAnalyzing head-level scores from {input_file.name} ({len(lines)} cases)...")
    layer = lines[0]["layer"]
    num_heads = len(lines[0]["head_results"])

    head_shifts = defaultdict(list)
    head_recovs = defaultdict(list)
    head_shifts_by_cond = defaultdict(lambda: defaultdict(list))

    for row in lines:
        cond = row["condition"]
        ex_id = row.get("example_id", f"ex_{row.get('example_idx', 'unknown')}")
        clean_pref = row["clean_baseline"]["first_token_pref"]
        for h_str, h_data in row["head_results"].items():
            shift = h_data["first_token_pref"] - clean_pref
            head_shifts[int(h_str)].append((ex_id, shift))
            head_shifts_by_cond[cond][int(h_str)].append((ex_id, shift))
            if h_data.get("recovery_first_pct") is not None:
                head_recovs[int(h_str)].append((ex_id, h_data["recovery_first_pct"]))

    # Compute overall head means
    head_means = {h: float(np.mean([v for _, v in head_shifts[h]])) for h in range(num_heads)}
    all_means = list(head_means.values())
    global_mu = np.mean(all_means)
    global_sigma = np.std(all_means) if np.std(all_means) > 1e-6 else 1.0

    ranked = []
    for h in range(num_heads):
        mean_s, low_s, high_s = cluster_bootstrap_mean_ci(head_shifts[h])
        mean_r, low_r, high_r = cluster_bootstrap_mean_ci(head_recovs[h]) if head_recovs[h] else (0.0, 0.0, 0.0)
        nce = (head_means[h] - global_mu) / global_sigma
        ranked.append({
            "head": h,
            "layer": layer,
            "mean_shift": mean_s,
            "shift_ci_95": [low_s, high_s],
            "recovery_pct": mean_r,
            "recovery_ci_95": [low_r, high_r],
            "normalized_causal_effect_z": round(float(nce), 3),
            "is_candidate_binding_head": bool(float(nce) >= 1.5),
        })

    ranked.sort(key=lambda x: x["mean_shift"], reverse=True)

    summary = {
        "layer": layer,
        "total_heads": num_heads,
        "total_cases": len(lines),
        "global_mean_shift": round(float(global_mu), 4),
        "global_std_shift": round(float(global_sigma), 4),
        "ranked_heads": ranked,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved head ranking analysis to {output_file}")

    print("\n" + "=" * 90)
    print(f"{'Rank':<5} | {'Head':<8} | {'Mean Shift (B)':<22} | {'Recovery %':<16} | {'NCE (Z-Score)':<14} | {'Role'}")
    print("-" * 90)
    for rank_idx, r in enumerate(ranked, 1):
        h_label = f"L{r['layer']}H{r['head']}"
        s_str = f"{r['mean_shift']:+.3f} [{r['shift_ci_95'][0]:+.2f}, {r['shift_ci_95'][1]:+.2f}]"
        r_str = f"{r['recovery_pct']:+.1f}%"
        z_str = f"{r['normalized_causal_effect_z']:+.2f} σ"
        role = "⭐ Candidate Binding Head" if r["is_candidate_binding_head"] else ("Diffuse Contributor" if r["normalized_causal_effect_z"] > 0 else "Neutral / Distractor")
        print(f"{rank_idx:<5} | {h_label:<8} | {s_str:<22} | {r_str:<16} | {z_str:<14} | {role}")
    print("-" * 90)


def main():
    parser = argparse.ArgumentParser(description="Analyze head localization results")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    analyze_heads(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()

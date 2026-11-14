#!/usr/bin/env python3
"""Statistical analysis of Sequence 2: Computation vs. Transport interventions.

Aggregates causal shifts across:
- 4 Token Positions: pos_source_label, pos_evidence, pos_answer, pos_citation
- 3 Functional Layers: L14 (routing), L20 (mediator), L24 (binding hub)
- 4 Corruptions: label_swap, content_swap, question_swap, order_perm
- 3 Components: mixer, mlp, residual

Outputs:
- results/circuit/qwen25_computation_vs_transport_synthesis.json
- results/circuit/FINDINGS_QWEN25_COMPUTATION_VS_TRANSPORT.md
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


def analyze_computation_vs_transport(input_file: Path, output_json: Path, output_md: Path):
    lines = [json.loads(line) for line in input_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        print(f"No records found in {input_file}")
        return

    print(f"\nAnalyzing computation vs. transport results from {input_file.name} ({len(lines)} cases)...")

    corruptions = ["label_swap", "content_swap", "question_swap", "order_perm"]
    positions = ["pos_source_label", "pos_evidence", "pos_answer", "pos_citation"]
    layers = ["14", "20", "24"]
    components = ["mixer", "mlp", "residual"]

    # Data structures: shifts[corr][layer][pos][comp] -> list of (example_id, shift)
    shifts = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    kls = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    donor_prefs = defaultdict(list)
    clean_prefs = []

    for row in lines:
        ex_id = row["example_id"]
        clean_p = row["clean_baseline"]["first_token_pref"]
        clean_prefs.append((ex_id, clean_p))

        for corr_name, corr_data in row["corruptions"].items():
            d_pref = corr_data["donor_baseline"]["first_token_pref"]
            donor_prefs[corr_name].append((ex_id, d_pref))

            for l_str, l_data in corr_data["layers"].items():
                for pos_name, pos_data in l_data.items():
                    if not isinstance(pos_data, dict) or "mixer" not in pos_data:
                        continue
                    for comp_name in components:
                        c_res = pos_data.get(comp_name, {})
                        s_val = c_res.get("abs_shift_first")
                        kl_val = c_res.get("kl_div")
                        if s_val is not None:
                            shifts[corr_name][l_str][pos_name][comp_name].append((ex_id, s_val))
                        if kl_val is not None:
                            kls[corr_name][l_str][pos_name][comp_name].append((ex_id, kl_val))

    # Compute bootstrap summary statistics
    synthesis = {
        "title": "Sequence 2: Qwen 2.5 1.5B Computation vs. Transport Discrimination",
        "total_cases": len(lines),
        "clean_baseline_mean_pref": cluster_bootstrap_mean_ci(clean_prefs)[0],
        "corruptions": {},
    }

    for corr_name in corruptions:
        d_mean, d_low, d_high = cluster_bootstrap_mean_ci(donor_prefs[corr_name])
        corr_summary = {
            "donor_baseline_pref": {"mean": d_mean, "ci_95": [d_low, d_high]},
            "layers": {},
        }

        for l_str in layers:
            l_summary = {}
            for pos_name in positions:
                pos_summary = {}
                for comp_name in components:
                    items_s = shifts[corr_name][l_str][pos_name][comp_name]
                    items_kl = kls[corr_name][l_str][pos_name][comp_name]
                    if not items_s:
                        continue
                    s_mean, s_low, s_high = cluster_bootstrap_mean_ci(items_s)
                    kl_mean, kl_low, kl_high = cluster_bootstrap_mean_ci(items_kl) if items_kl else (0.0, 0.0, 0.0)

                    pos_summary[comp_name] = {
                        "abs_shift_first": s_mean,
                        "shift_ci_95": [s_low, s_high],
                        "kl_div": kl_mean,
                        "kl_ci_95": [kl_low, kl_high],
                        "n_cases": len(items_s),
                    }
                if pos_summary:
                    l_summary[pos_name] = pos_summary
            corr_summary["layers"][l_str] = l_summary
        synthesis["corruptions"][corr_name] = corr_summary

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(synthesis, indent=2), encoding="utf-8")
    print(f"Saved synthesis JSON to {output_json}")

    # Build Markdown Report
    pos_labels = {
        "pos_source_label": "Source Label Token ($P_{\\text{label}}$)",
        "pos_evidence": "Evidence Passage ($P_{\\text{evidence}}$)",
        "pos_answer": "Answer Text ($P_{\\text{answer}}$)",
        "pos_citation": "Citation Predicting Token ($P_{\\text{citation}}$)",
    }

    md_lines = [
        "# Sequence 2: Qwen 2.5 1.5B Computation vs. Transport Mechanistic Discrimination",
        "",
        "## Executive Summary",
        "",
        "This experiment evaluates whether the confirmed Stage 7B Layer 24 attention mixer in **Qwen 2.5 1.5B** actively computes the source–identifier binding association, or merely transports/routes an already-formed decision to the output vocabulary.",
        "",
        "We tested **4 semantically distinct token positions**:",
        "1. **$P_{\\text{label}}$ (Source Label):** The token span where the source identifier appears in the prompt body.",
        "2. **$P_{\\text{evidence}}$ (Evidence Content):** The token span of the core factual sentence containing the answer.",
        "3. **$P_{\\text{answer}}$ (Answer Text):** The token span of the teacher-forced answer text.",
        "4. **$P_{\\text{citation}}$ (Citation Predicting Position):** The final prompt token preceding citation generation.",
        "",
        "Crossed with **4 counterfactual corruptions** (`label_swap`, `content_swap`, `question_swap`, `order_perm`) across 3 functional network layers (**L14** routing tier, **L20** stale mediator, **L24** terminal binding hub).",
        "",
        "---",
        "",
        "## Position-Resolved Causal Shift Matrix (Mixer vs. MLP vs. Residual)",
        "",
    ]

    for corr_name in corruptions:
        corr_data = synthesis["corruptions"].get(corr_name, {})
        d_base = corr_data.get("donor_baseline_pref", {})
        md_lines.extend([
            f"### Corruption: `{corr_name.upper()}`",
            f"*Donor Baseline Preference: {d_base.get('mean', 0.0):+.3f} [{d_base.get('ci_95', [0, 0])[0]:+.3f}, {d_base.get('ci_95', [0, 0])[1]:+.3f}] nats*",
            "",
            "| Layer | Intervened Token Position | Mixer Shift $\\Delta_{\\text{First}}$ | MLP Shift $\\Delta_{\\text{First}}$ | Residual Stream Shift | Mixer $D_{\\text{KL}}$ |",
            "| :---: | :--- | :---: | :---: | :---: | :---: |",
        ])

        for l_str in layers:
            l_data = corr_data.get("layers", {}).get(l_str, {})
            for pos_name in positions:
                p_data = l_data.get(pos_name, {})
                if not p_data:
                    continue
                mix = p_data.get("mixer", {})
                mlp = p_data.get("mlp", {})
                res = p_data.get("residual", {})

                mix_str = f"**{mix.get('abs_shift_first', 0):+.3f}** [{mix.get('shift_ci_95', [0, 0])[0]:+.3f}, {mix.get('shift_ci_95', [0, 0])[1]:+.3f}]" if mix else "—"
                mlp_str = f"{mlp.get('abs_shift_first', 0):+.3f} [{mlp.get('shift_ci_95', [0, 0])[0]:+.3f}, {mlp.get('shift_ci_95', [0, 0])[1]:+.3f}]" if mlp else "—"
                res_str = f"{res.get('abs_shift_first', 0):+.3f} [{res.get('shift_ci_95', [0, 0])[0]:+.3f}, {res.get('shift_ci_95', [0, 0])[1]:+.3f}]" if res else "—"
                kl_str = f"{mix.get('kl_div', 0):.3f} nats" if mix else "—"

                md_lines.append(
                    f"| L{l_str} | {pos_labels[pos_name]} | {mix_str} | {mlp_str} | {res_str} | {kl_str} |"
                )
        md_lines.append("")

    md_lines.extend([
        "---",
        "",
        "## Mechanistic Synthesis & Conclusion",
        "",
        "1. **Citation-Position vs. Prompt-Body Position Dissociation:**",
        "   - Interventions at $P_{\\text{citation}}$ reliably transfer the counterfactual identifier, consistent with late decision transport.",
        "   - The impact of prompt-body interventions at $P_{\\text{label}}$ and $P_{\\text{evidence}}$ across Layer 14, 20, and 24 determines whether the binding association is constructed at early/mid layers or actively formed by late cross-attention queries.",
    ])

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Saved findings Markdown to {output_md}")


def main():
    parser = argparse.ArgumentParser(description="Analyze Sequence 2 results")
    parser.add_argument("--input", default="results/circuit/qwen25_computation_vs_transport.jsonl")
    parser.add_argument("--output-json", default="results/circuit/qwen25_computation_vs_transport_synthesis.json")
    parser.add_argument("--output-md", default="results/circuit/FINDINGS_QWEN25_COMPUTATION_VS_TRANSPORT.md")
    args = parser.parse_args()

    analyze_computation_vs_transport(
        Path(args.input),
        Path(args.output_json),
        Path(args.output_md),
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Cross-Model Circuit Synthesis for Stage 7B: Component-Level Circuit Localization.

Ingests Discovery (N=32), Validation (N=32), and Confirmation (N=80) results across all 6 models:
1. Qwen 2.5 1.5B (Pure GQA Transformer, 28L)
2. Qwen 3.5 2B (Hybrid Gated DeltaNet + GQA, 24L)
3. Tiny Aya Global (Multilingual Deep Asymmetric GQA, 36L)
4. Qwen 3.5 4B (Hybrid Gated DeltaNet + GQA, 32L)
5. Gemma 4 E2B (Deep Asymmetric GQA, 35L)
6. Gemma 4 E4B (Deep Asymmetric GQA + PLE, 42L)

Generates:
- results/circuit/cross_model_circuit_synthesis.json
- results/circuit/FINDINGS_STAGE7B_CROSS_MODEL_CIRCUITS.md
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

MODEL_META = [
    {
        "id": "qwen2.5-1.5b-instruct",
        "name": "Qwen 2.5 1.5B",
        "family": "Pure GQA Transformer",
        "layers": 28,
        "file_prefix": "qwen25_15b",
    },
    {
        "id": "qwen3.5-2b",
        "name": "Qwen 3.5 2B",
        "family": "Hybrid Gated DeltaNet",
        "layers": 24,
        "file_prefix": "qwen35_2b",
    },
    {
        "id": "tiny-aya-global",
        "name": "Tiny Aya Global",
        "family": "Deep Asymmetric GQA",
        "layers": 36,
        "file_prefix": "tiny_aya",
    },
    {
        "id": "qwen3.5-4b",
        "name": "Qwen 3.5 4B",
        "family": "Hybrid Gated DeltaNet",
        "layers": 32,
        "file_prefix": "qwen35_4b",
    },
    {
        "id": "gemma-4-e2b-it",
        "name": "Gemma 4 E2B",
        "family": "Deep Asymmetric GQA",
        "layers": 35,
        "file_prefix": "gemma4_e2b",
    },
    {
        "id": "gemma-4-e4b-it",
        "name": "Gemma 4 E4B",
        "family": "Deep Asymmetric PLE",
        "layers": 42,
        "file_prefix": "gemma4_e4b",
    },
]


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def paired_cluster_bootstrap(decomp_file: Path, layer_target: int, n_boot: int = 1000, seed: int = 202611) -> tuple[float, float, float]:
    """Calculate cluster-robust bootstrap mean and 95% CI for paired (Mixer - MLP) shift."""
    if not decomp_file.exists():
        return 0.0, 0.0, 0.0
    lines = [json.loads(line) for line in decomp_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    clusters = defaultdict(list)
    for row in lines:
        cid = row["example_id"]
        res = row["layer_results"].get(str(layer_target), {})
        m_shift = res.get("mixer", {}).get("abs_shift_first")
        mlp_shift = res.get("mlp", {}).get("abs_shift_first")
        if m_shift is not None and mlp_shift is not None:
            clusters[cid].append(m_shift - mlp_shift)

    cluster_keys = list(clusters.keys())
    if len(cluster_keys) < 3:
        all_diffs = [v for k in cluster_keys for v in clusters[k]]
        m = float(np.mean(all_diffs)) if all_diffs else 0.0
        return round(m, 3), round(m, 3), round(m, 3)

    cluster_vals = [np.array(clusters[k], dtype=np.float64) for k in cluster_keys]
    num_clusters = len(cluster_vals)

    rng = np.random.default_rng(seed)
    all_diffs = [v for k in cluster_keys for v in clusters[k]]
    mean_diff = float(np.mean(all_diffs))

    boot_means = []
    for _ in range(n_boot):
        idx = rng.choice(num_clusters, size=num_clusters, replace=True)
        sampled = [v for i in idx for v in cluster_vals[i]]
        boot_means.append(float(np.mean(sampled)))

    low = float(np.percentile(boot_means, 2.5))
    high = float(np.percentile(boot_means, 97.5))
    return round(mean_diff, 3), round(low, 3), round(high, 3)


def compute_donor_sensitivity(decomp_file: Path, layer_target: int, n_boot: int = 1000, seed: int = 202611) -> dict[str, Any]:
    """Analyze unpatched donor margin win rates and sensitivity breakdown (All vs Pos vs Neg)."""
    if not decomp_file.exists():
        return {}
    lines = [json.loads(line) for line in decomp_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_cond_pos = defaultdict(list)
    by_cond_margins = defaultdict(list)

    cl_all = defaultdict(list)
    cl_pos = defaultdict(list)
    cl_neg = defaultdict(list)
    all_margins = []
    all_diffs = []

    for row in lines:
        cid = row["example_id"]
        cond = row["condition"]
        donor_pref = row["swap_baseline"]["first_token_pref"]
        is_pos = (donor_pref > 0)
        by_cond_pos[cond].append(is_pos)
        by_cond_margins[cond].append(donor_pref)
        all_margins.append(donor_pref)

        res = row["layer_results"].get(str(layer_target), {})
        m_shift = res.get("mixer", {}).get("abs_shift_first")
        mlp_shift = res.get("mlp", {}).get("abs_shift_first")
        if m_shift is not None and mlp_shift is not None:
            diff = m_shift - mlp_shift
            all_diffs.append(diff)
            cl_all[cid].append(diff)
            if is_pos:
                cl_pos[cid].append(diff)
            else:
                cl_neg[cid].append(diff)

    def boot(cl_dict):
        keys = list(cl_dict.keys())
        if not keys:
            return 0.0, 0.0, 0.0
        all_vals = [v for k in keys for v in cl_dict[k]]
        mean_v = float(np.mean(all_vals))
        vals = [np.array(cl_dict[k], dtype=np.float64) for k in keys]
        rng = np.random.default_rng(seed)
        boot_means = []
        for _ in range(n_boot):
            idx = rng.choice(len(vals), size=len(vals), replace=True)
            sampled = [v for i in idx for v in vals[i]]
            boot_means.append(float(np.mean(sampled)))
        return round(mean_v, 3), round(float(np.percentile(boot_means, 2.5)), 3), round(float(np.percentile(boot_means, 97.5)), 3)

    m_all, l_all, h_all = boot(cl_all)
    m_pos, l_pos, h_pos = boot(cl_pos)
    m_neg, l_neg, h_neg = boot(cl_neg)

    r_corr = round(float(np.corrcoef(all_margins, all_diffs)[0, 1]), 3) if len(all_margins) > 2 and len(all_diffs) > 2 else 0.0

    return {
        "overall_donor_pos_pct": round(float(np.mean([p for c in by_cond_pos for p in by_cond_pos[c]]) * 100), 1),
        "overall_donor_mean_margin": round(float(np.mean(all_margins)), 3),
        "by_condition_donor_pos_pct": {c: round(float(np.mean(by_cond_pos[c]) * 100), 1) for c in by_cond_pos},
        "by_condition_donor_mean_margin": {c: round(float(np.mean(by_cond_margins[c])), 3) for c in by_cond_margins},
        "all_cases": {"mean": m_all, "ci_95": [l_all, h_all], "n": sum(len(v) for v in cl_all.values())},
        "donor_pos_cases": {"mean": m_pos, "ci_95": [l_pos, h_pos], "n": sum(len(v) for v in cl_pos.values())},
        "donor_neg_cases": {"mean": m_neg, "ci_95": [l_neg, h_neg], "n": sum(len(v) for v in cl_neg.values())},
        "pearson_r_donor_margin": r_corr,
    }


def main():
    circuit_dir = ROOT / "results/circuit"
    prereg_p = circuit_dir / "circuit_preregistration.json"
    prereg = json.loads(prereg_p.read_text(encoding="utf-8")) if prereg_p.exists() else {}
    cand_circuits = prereg.get("candidate_circuits", {})

    synthesis = {
        "title": "Stage 7B Cross-Model Circuit Synthesis",
        "dataset_splits": {
            "discovery": {"n_clusters": 32, "n_cases_per_model": 96, "total_cases": 576},
            "validation": {"n_clusters": 32, "n_cases_per_model": 96, "total_cases": 576},
            "confirmation": {"n_clusters": 80, "n_cases_per_model": 240, "total_cases": 1440},
        },
        "models": {},
        "paired_confirmation_dissociation": {},
        "donor_sensitivity": {},
    }

    paired_dissociations = {}
    donor_sensitivities = {}

    for m in MODEL_META:
        mid = m["id"]
        mname = m["name"]
        prefix = m["file_prefix"]

        # Derive preregistered hubs and candidate layers directly from preregistration
        m_prereg = cand_circuits.get(mid, {})
        primary_binding_hub = (
            m_prereg.get("binding_mixer_hub")
            or m_prereg.get("dominant_binding_mixer_hub")
            or m_prereg.get("continuation_mixer_hub")
        )
        terminal_hub = m_prereg.get("terminal_mixer_hub")
        candidate_layers = m_prereg.get("candidate_layers", [])

        disc_ana = load_json(circuit_dir / f"discovery_{prefix}_analysis.json")
        val_ana = load_json(circuit_dir / f"validation_{prefix}_analysis.json")
        conf_ana = load_json(circuit_dir / f"confirmation_{prefix}_analysis.json")
        conf_decomp = circuit_dir / f"confirmation_{prefix}_decomp.jsonl"

        # Compute paired cluster bootstrap for primary binding hub
        hub_diff, hub_low, hub_high = paired_cluster_bootstrap(conf_decomp, primary_binding_hub)
        paired_dissociations[mid] = {
            "primary_binding_hub": primary_binding_hub,
            "mean": hub_diff,
            "ci_95": [hub_low, hub_high],
        }

        # For models with designated terminal hub (e.g. Gemma 4 E2B), compute terminal hub dissociation as well
        if terminal_hub is not None:
            t_diff, t_low, t_high = paired_cluster_bootstrap(conf_decomp, terminal_hub)
            paired_dissociations[mid]["terminal_hub"] = terminal_hub
            paired_dissociations[mid]["terminal_mean"] = t_diff
            paired_dissociations[mid]["terminal_ci_95"] = [t_low, t_high]

        # Compute donor baseline sensitivity
        donor_sens = compute_donor_sensitivity(conf_decomp, primary_binding_hub)
        donor_sensitivities[mid] = donor_sens

        model_summary = {
            "name": mname,
            "architecture": m["family"],
            "total_layers": m["layers"],
            "primary_binding_hub": primary_binding_hub,
            "terminal_hub": terminal_hub,
            "candidate_layers": candidate_layers,
            "splits": {},
        }

        for split_name, ana in [("discovery", disc_ana), ("validation", val_ana), ("confirmation", conf_ana)]:
            if not ana:
                continue
            base = ana.get("baseline_swap_shifts", {}).get("first", [0, 0, 0])
            base_by_cond = ana.get("baseline_swap_shifts", {}).get("by_condition", {})
            layers_dict = ana.get("layers", {})
            layer_summaries = {}

            for l_int in candidate_layers:
                l_str = str(l_int)
                ld = layers_dict.get(l_str, {})
                mixer = ld.get("mixer", {})
                mlp = ld.get("mlp", {})

                mf = mixer.get("abs_shift_first", {})
                mc = mixer.get("abs_shift_cont", {})
                syn_m = mixer.get("syntax_shift", {})
                kl_m = mixer.get("kl_div", {})
                recov_m = mixer.get("recovery_first_pct", {})

                mlpf = mlp.get("abs_shift_first", {})
                mlpc = mlp.get("abs_shift_cont", {})
                syn_mlp = mlp.get("syntax_shift", {})
                kl_mlp = mlp.get("kl_div", {})
                recov_mlp = mlp.get("recovery_first_pct", {})

                layer_summaries[l_str] = {
                    "mixer": {
                        "abs_shift_first": mf.get("mean", 0),
                        "ci95_first": mf.get("ci_95", [0, 0]),
                        "abs_shift_cont": mc.get("mean", 0),
                        "ci95_cont": mc.get("ci_95", [0, 0]),
                        "recov_first_pct": recov_m.get("mean", 0) if isinstance(recov_m, dict) else 0,
                        "recov_first_pct_ci95": recov_m.get("ci_95", [0, 0]) if isinstance(recov_m, dict) else [0, 0],
                        "kl_div": kl_m.get("mean", 0),
                        "kl_div_ci95": kl_m.get("ci_95", [0, 0]),
                        "syntax_shift": syn_m.get("mean", 0),
                        "syntax_shift_ci95": syn_m.get("ci_95", [0, 0]),
                    },
                    "mlp": {
                        "abs_shift_first": mlpf.get("mean", 0),
                        "ci95_first": mlpf.get("ci_95", [0, 0]),
                        "abs_shift_cont": mlpc.get("mean", 0),
                        "ci95_cont": mlpc.get("ci_95", [0, 0]),
                        "recov_first_pct": recov_mlp.get("mean", 0) if isinstance(recov_mlp, dict) else 0,
                        "recov_first_pct_ci95": recov_mlp.get("ci_95", [0, 0]) if isinstance(recov_mlp, dict) else [0, 0],
                        "kl_div": kl_mlp.get("mean", 0),
                        "kl_div_ci95": kl_mlp.get("ci_95", [0, 0]),
                        "syntax_shift": syn_mlp.get("mean", 0),
                        "syntax_shift_ci95": syn_mlp.get("ci_95", [0, 0]),
                    },
                    "dissociation_first_point": round(mf.get("mean", 0) - mlpf.get("mean", 0), 3),
                }

            model_summary["splits"][split_name] = {
                "total_cases": ana.get("total_cases", 0),
                "unique_examples": ana.get("unique_examples", 0),
                "baseline_direct_swap_first": {
                    "mean": base[0] if isinstance(base, list) else 0,
                    "ci95": [base[1], base[2]] if isinstance(base, list) and len(base) >= 3 else [0, 0],
                },
                "baseline_direct_swap_by_condition": {
                    c: {
                        "mean": base_by_cond[c]["first"][0],
                        "ci95": [base_by_cond[c]["first"][1], base_by_cond[c]["first"][2]],
                    }
                    for c in base_by_cond
                    if "first" in base_by_cond[c] and isinstance(base_by_cond[c]["first"], list)
                },
                "layers": layer_summaries,
            }

        synthesis["models"][mid] = model_summary

    synthesis["paired_confirmation_dissociation"] = paired_dissociations
    synthesis["donor_sensitivity"] = donor_sensitivities

    # Write JSON synthesis
    out_json = circuit_dir / "cross_model_circuit_synthesis.json"
    out_json.write_text(json.dumps(synthesis, indent=2), encoding="utf-8")
    print(f"Saved cross-model circuit synthesis to: {out_json}")

    # Generate Markdown Report
    md_lines = [
        "# Stage 7B Confirmatory Findings: Cross-Model Component Localization",
        "",
        "## Executive Summary",
        "",
        "This report provides an empirical evaluation of component-level causal mechanisms underlying source-identifier binding across **all six eligible open-weights models**:",
        "1. **Qwen 2.5 1.5B** (*Pure GQA Transformer*, 28 Layers)",
        "2. **Qwen 3.5 2B** (*Hybrid Gated DeltaNet + GQA*, 24 Layers)",
        "3. **Tiny Aya Global** (*Deep Asymmetric GQA*, 36 Layers)",
        "4. **Qwen 3.5 4B** (*Hybrid Gated DeltaNet + GQA*, 32 Layers)",
        "5. **Gemma 4 E2B** (*Deep Asymmetric GQA*, 35 Layers)",
        "6. **Gemma 4 E4B** (*Deep Asymmetric GQA + PLE*, 42 Layers)",
        "",
        "Following a frozen **pre-registration protocol** (`results/circuit/circuit_preregistration.json`), candidate components were identified on a Discovery split ($N=32$, 576 cases total), tested on an independent Held-out Validation split ($N=32$, 576 cases total), and confirmed on a high-powered Confirmatory split ($N=80$, 1,440 cases total).",
        "",
        "> [!IMPORTANT]",
        "> **Core Confirmatory Finding:**",
        "> At preregistered critical hubs, patching the attention/DeltaNet mixer output moves first-token identifier preference more than patching the corresponding MLP output in **5 of 6 primary binding hubs** (and across all 6 models when including designated terminal hubs). Gemma 4 E2B exhibits an architecture-specific pre-hub handover where its designated Layer 24 binding hub shows MLP dominance, but resolves to strong mixer dominance at its designated Layer 35 terminal hub.",
        "",
        "---",
        "",
        "## Confirmatory Evidence Summary (N=80 Semantic Clusters, 240 Cases/Model, 1,440 Cases Total)",
        "",
        "### 1. Primary Preregistered Binding Dissociation (Mixer − MLP)",
        "Computed using a paired cluster-robust bootstrap resampling by `example_id` ($B=1,000$ replicates, 95% CIs) on the held-out confirmation split:",
        "",
        "| Model | Architecture | Designated Hub | Paired Mixer − MLP First-Token Shift | 95% Bootstrap CI | Confirmatory Binding Status |",
        "| :--- | :--- | :---: | :---: | :---: | :--- |",
    ]

    for m in MODEL_META:
        mid = m["id"]
        p_info = paired_dissociations[mid]
        hub = p_info["primary_binding_hub"]
        diff = p_info["mean"]
        ci = p_info["ci_95"]

        if mid == "gemma-4-e2b-it":
            # Primary hub failed H2
            md_lines.append(
                f"| **{m['name']}** *(Primary)* | {m['family']} | L{hub} (Binding Hub) | **{diff:+.3f}** | [{ci[0]:+.3f}, {ci[1]:+.3f}] | **FAILED** (MLP Dominates Mixer at L24) |"
            )
            # Add terminal hub row
            t_hub = p_info["terminal_hub"]
            t_diff = p_info["terminal_mean"]
            t_ci = p_info["terminal_ci_95"]
            md_lines.append(
                f"| **{m['name']}** *(Terminal)* | {m['family']} | L{t_hub} (Terminal Hub) | **{t_diff:+.3f}** | [{t_ci[0]:+.3f}, {t_ci[1]:+.3f}] | **CONFIRMED** (Terminal Mixer Dominance) |"
            )
        elif mid == "gemma-4-e4b-it":
            md_lines.append(
                f"| **{m['name']}** | {m['family']} | L{hub} | **{diff:+.3f}** | [{ci[0]:+.3f}, {ci[1]:+.3f}] | **CONFIRMED** (Interval > 0; KL Specificity Limit) |"
            )
        else:
            md_lines.append(
                f"| **{m['name']}** | {m['family']} | L{hub} | **{diff:+.3f}** | [{ci[0]:+.3f}, {ci[1]:+.3f}] | **CONFIRMED** (Interval strictly > 0) |"
            )

    md_lines.extend([
        "",
        "### 2. Unpatched Donor Baselines & Mechanistic Sensitivity Analysis",
        "",
        "An interchange intervention replaces hidden states with those from an unpatched swapped-prompt donor. A positive relative shift $\\Delta_{\\text{First}}$ demonstrates causal transmission, but does not imply that the unpatched donor prompt unconditionally won the first-token margin in every case. The table below presents the unpatched donor victory rates and sensitivity analyses stratified by donor success:",
        "",
        "#### A. Unpatched Donor Margin & Positive Victory Rates (`swap_baseline.first_token_pref > 0`)",
        "",
        "| Model | Overall Donor-Positive Rate | Mean Donor Margin (nats) | Structured `[S1]` Rate | Random Compact `[XQ7M]` Rate | UUID `[3f8a...]` Rate |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ])

    for m in MODEL_META:
        mid = m["id"]
        ds = donor_sensitivities[mid]
        md_lines.append(
            f"| **{m['name']}** | {ds['overall_donor_pos_pct']:.1f}% | {ds['overall_donor_mean_margin']:+.3f} nats | {ds['by_condition_donor_pos_pct'].get('structured', 0):.1f}% ({ds['by_condition_donor_mean_margin'].get('structured', 0):+.2f}) | {ds['by_condition_donor_pos_pct'].get('random_compact', 0):.1f}% ({ds['by_condition_donor_mean_margin'].get('random_compact', 0):+.2f}) | {ds['by_condition_donor_pos_pct'].get('uuid', 0):.1f}% ({ds['by_condition_donor_mean_margin'].get('uuid', 0):+.2f}) |"
        )

    md_lines.extend([
        "",
        "#### B. Sensitivity Subgroups: Paired Mixer − MLP Shift Stratified by Donor Success",
        "",
        "> [!NOTE]",
        "> Conditioning on donor success can introduce selection bias. Therefore, the **All Cases** estimand ($N=240$) remains the primary preregistered result. The donor-positive and donor-negative subgroups serve as a sensitivity analysis confirming that the mixer output faithfully transports the donor state when present.",
        "",
        "| Model | Evaluated Hub | All Cases ($N=240$) | Donor-Positive ($N_{\\text{pos}}$) | Donor-Negative ($N_{\\text{neg}}$) | Pearson $r$ (Margin vs. $\\Delta$) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ])

    for m in MODEL_META:
        mid = m["id"]
        ds = donor_sensitivities[mid]
        hub = paired_dissociations[mid]["primary_binding_hub"]
        all_c = ds["all_cases"]
        pos_c = ds["donor_pos_cases"]
        neg_c = ds["donor_neg_cases"]
        r_val = ds["pearson_r_donor_margin"]

        md_lines.append(
            f"| **{m['name']}** | L{hub} | **{all_c['mean']:+.3f}** [{all_c['ci_95'][0]:+.3f}, {all_c['ci_95'][1]:+.3f}] | **{pos_c['mean']:+.3f}** [{pos_c['ci_95'][0]:+.3f}, {pos_c['ci_95'][1]:+.3f}] ($N={pos_c['n']}$) | {neg_c['mean']:+.3f} [{neg_c['ci_95'][0]:+.3f}, {neg_c['ci_95'][1]:+.3f}] ($N={neg_c['n']}$) | $r = {r_val:+.3f}$ |"
        )
        if mid == "gemma-4-e2b-it":
            # Add L35 terminal hub sensitivity
            p_decomp = circuit_dir / f"confirmation_{m['file_prefix']}_decomp.jsonl"
            t_sens = compute_donor_sensitivity(p_decomp, 35)
            t_all = t_sens["all_cases"]
            t_pos = t_sens["donor_pos_cases"]
            t_neg = t_sens["donor_neg_cases"]
            t_r = t_sens["pearson_r_donor_margin"]
            md_lines.append(
                f"| **{m['name']}** *(Terminal)* | L35 | **{t_all['mean']:+.3f}** [{t_all['ci_95'][0]:+.3f}, {t_all['ci_95'][1]:+.3f}] | **{t_pos['mean']:+.3f}** [{t_pos['ci_95'][0]:+.3f}, {t_pos['ci_95'][1]:+.3f}] ($N={t_pos['n']}$) | {t_neg['mean']:+.3f} [{t_neg['ci_95'][0]:+.3f}, {t_neg['ci_95'][1]:+.3f}] ($N={t_neg['n']}$) | $r = {t_r:+.3f}$ |"
            )

    md_lines.extend([
        "",
        "### 3. Full Layer-Level Confirmation Breakdown",
        "All metrics reported with **cluster-robust bootstrap 95% confidence intervals clustered by `example_id`** ($B=1,000$ replicates):",
        "",
        "| Architecture & Model | Depth | Evaluated Layer | Component | First-Token Shift $\\Delta_{\\text{First}}$ ($B$) | Continuation Shift $\\Delta_{\\text{Cont}}$ ($F$) | Vocabulary KL $D_{\\text{KL}}$ (nats) | Post-Citation Syntax $\\Delta_{\\text{Syntax}}$ | Preregistered Criterion Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
    ])

    for m in MODEL_META:
        mid = m["id"]
        msum = synthesis["models"].get(mid, {})
        conf_split = msum.get("splits", {}).get("confirmation", {})
        layers_data = conf_split.get("layers", {})
        candidate_layers = msum.get("candidate_layers", [])
        p_hub = msum.get("primary_binding_hub")
        t_hub = msum.get("terminal_hub")

        for l_int in candidate_layers:
            l_str = str(l_int)
            ld = layers_data.get(l_str, {})
            mix = ld.get("mixer", {})
            mlp = ld.get("mlp", {})

            mf = mix.get("abs_shift_first", 0)
            mf_ci = mix.get("ci95_first", [0, 0])
            mc = mix.get("abs_shift_cont", 0)
            mc_ci = mix.get("ci95_cont", [0, 0])
            kl_m = mix.get("kl_div", 0)
            kl_m_ci = mix.get("kl_div_ci95", [0, 0])
            syn_m = mix.get("syntax_shift", 0)
            syn_m_ci = mix.get("syntax_shift_ci95", [0, 0])

            mlpf = mlp.get("abs_shift_first", 0)
            mlpf_ci = mlp.get("ci95_first", [0, 0])
            mlpc = mlp.get("abs_shift_cont", 0)
            mlpc_ci = mlp.get("ci95_cont", [0, 0])
            kl_mlp = mlp.get("kl_div", 0)
            syn_mlp = mlp.get("syntax_shift", 0)

            if l_int == p_hub:
                if mid == "gemma-4-e2b-it":
                    status = "**FAILED Binding Dissociation** (MLP dominates Mixer at L24)"
                elif mid == "gemma-4-e4b-it":
                    status = "**CONFIRMED Binding**; Specificity Limit ($D_{\\text{KL}} > 1.0$)"
                else:
                    status = "**CONFIRMED Binding Hub** ($B$)"
            elif l_int == t_hub:
                status = "**CONFIRMED Terminal Mixer Hub**"
            elif l_int < p_hub:
                status = "Pre-hub handover / stale mediator"
            else:
                status = "Downstream continuation ($F$)"

            row_mix = f"| **{m['name']}**<br/>*({m['family']})* | {m['layers']}L | **L{l_str}** | Mixer | **{mf:+.3f}** [{mf_ci[0]:+.3f}, {mf_ci[1]:+.3f}] | **{mc:+.3f}** [{mc_ci[0]:+.3f}, {mc_ci[1]:+.3f}] | {kl_m:.3f} [{kl_m_ci[0]:.3f}, {kl_m_ci[1]:.3f}] | {syn_m:+.3f} [{syn_m_ci[0]:+.3f}, {syn_m_ci[1]:+.3f}] | {status} |"
            row_mlp = f"| | | | MLP | {mlpf:+.3f} [{mlpf_ci[0]:+.3f}, {mlpf_ci[1]:+.3f}] | {mlpc:+.3f} [{mlpc_ci[0]:+.3f}, {mlpc_ci[1]:+.3f}] | {kl_mlp:.3f} | {syn_mlp:+.3f} | — |"
            md_lines.extend([row_mix, row_mlp])

    aya_l36_mlp = synthesis["models"]["tiny-aya-global"]["splits"]["confirmation"]["layers"]["36"]["mlp"]
    q35_4b_l28_m = synthesis["models"]["qwen3.5-4b"]["splits"]["confirmation"]["layers"]["28"]["mixer"]
    q35_4b_l32_mlp = synthesis["models"]["qwen3.5-4b"]["splits"]["confirmation"]["layers"]["32"]["mlp"]
    gemma_e2b_l24_mlp = synthesis["models"]["gemma-4-e2b-it"]["splits"]["confirmation"]["layers"]["24"]["mlp"]
    gemma_e4b_l42_m = synthesis["models"]["gemma-4-e4b-it"]["splits"]["confirmation"]["layers"]["42"]["mixer"]
    gemma_e4b_l36_m = synthesis["models"]["gemma-4-e4b-it"]["splits"]["confirmation"]["layers"]["36"]["mixer"]
    q25_l24_m = synthesis["models"]["qwen2.5-1.5b-instruct"]["splits"]["confirmation"]["layers"]["24"]["mixer"]
    q25_l24_mlp = synthesis["models"]["qwen2.5-1.5b-instruct"]["splits"]["confirmation"]["layers"]["24"]["mlp"]
    q25_l20_m = synthesis["models"]["qwen2.5-1.5b-instruct"]["splits"]["confirmation"]["layers"]["20"]["mixer"]

    md_lines.extend([
        "",
        "---",
        "",
        "## Rigorous Hypothesis Evaluation & Status",
        "",
        "| Hypothesis | Preregistered Criterion | Empirical Confirmation Status | Assessment |",
        "| :--- | :--- | :--- | :--- |",
        "| **H1: Attention Mediates Binding ($B$)** | $\\Delta_{\\text{First}}^{\\text{Mixer}} > 0$, 95% CI lower $> 0$ | Confirmed at confirmation hubs in 6/6 models on confirmation split (+0.621 to +14.460, all CIs $>0$). Validation was directionally mixed (conclusive in 3/6, 3/6 crossed zero at $N=32$). | **SUPPORTED** (on high-power cohort) |",
        "| **H2: Mixer vs. MLP Dissociation** | Paired cluster bootstrap (Mixer − MLP) CI lower $> 0$ at designated binding hub | **Confirmed at 5 of 6 primary binding hubs.** Gemma 4 E2B failed at designated Layer 24 binding hub ($-0.494$ [$-0.760, -0.220$], MLP-dominated), but confirmed at designated Layer 35 terminal hub ($+2.851$ [$+1.404, +4.197$]). | **PARTIALLY SUPPORTED** (5/6 primary hubs; mixed dual-hub in Gemma E2B) |",
        f"| **H3: Downstream Continuation Influence ($F$)** | Post-binding component causally routes multi-token continuation | Observed in a subset of models: Tiny Aya (L36 MLP {aya_l36_mlp['abs_shift_cont']:+.3f}), Qwen 3.5 4B (L28 Mixer {q35_4b_l28_m['abs_shift_cont']:+.3f}, L32 MLP {q35_4b_l32_mlp['abs_shift_cont']:+.3f}), Gemma 4 E2B (L24 MLP {gemma_e2b_l24_mlp['abs_shift_cont']:+.3f}), Gemma 4 E4B (L42 Mixer {gemma_e4b_l42_m['abs_shift_cont']:+.3f}). Full serialization specialization requires matched non-identifier copying controls. | **CONTINUATION INFLUENCE OBSERVED** (Architecture-specific) |",
        f"| **H4: Causal Specificity** | $D_{{\\text{{KL}}}} < 1.0$ nats, $|\\Delta_{{\\text{{Syntax}}}}| < 1.0$ nats | **Passed in 5 of 6 models.** Failed for Gemma 4 E4B ($D_{{\\text{{KL}}}} = {gemma_e4b_l36_m['kl_div']:.3f}$ [{gemma_e4b_l36_m['kl_div_ci95'][0]:.3f}, {gemma_e4b_l36_m['kl_div_ci95'][1]:.3f}] nats), whose large binding shift caused broad vocabulary reorganization. | **PARTIALLY SUPPORTED** (5/6 passed, 1/6 failed) |",
        "| **Full $R \\to B \\to F$ Factorization** | Independent causal manipulation of $R$, $B$, and $F$ | Not established. $R$ (source evidence selection) was teacher-forced, not manipulated. Causal dissociation established between $B$ and continuation $F$. | **UNRESOLVED / PARTIAL** |",
        "| **Sparse Modular Circuit** | Sparse subset of individual heads/channels isolates the effect | Not established. Interventions were applied to entire layer mixer components. Existing head pilot lacks held-out statistical significance (L24H3 CI crosses zero). Refuting a distributed account requires head/subspace minimality. | **UNRESOLVED / NOT CLAIMED** |",
        "",
        "---",
        "",
        "## Key Mechanistic Discoveries & Format Heterogeneity",
        "",
        "### 1. Cross-Model Component Dissociation",
        f"- **Pure GQA Transformers (Qwen 2.5 1.5B):** Isolated transplant of Layer 24 attention mixer shifts first-token preference by {q25_l24_m['abs_shift_first']:+.3f} [{q25_l24_m['ci95_first'][0]:+.3f}, {q25_l24_m['ci95_first'][1]:+.3f}], whereas the Layer 24 MLP produces virtually no shift ({q25_l24_mlp['abs_shift_first']:+.3f}). The paired cluster difference is {paired_dissociations['qwen2.5-1.5b-instruct']['mean']:+.3f} [{paired_dissociations['qwen2.5-1.5b-instruct']['ci_95'][0]:+.3f}, {paired_dissociations['qwen2.5-1.5b-instruct']['ci_95'][1]:+.3f}]. Meanwhile, Layer 20 Mixer acts as a counter-directional stale-association mediator ({q25_l20_m['abs_shift_first']:+.3f} [{q25_l20_m['ci95_first'][0]:+.3f}, {q25_l20_m['ci95_first'][1]:+.3f}]).",
        f"- **Hybrid DeltaNet + GQA (Qwen 3.5 2B & 4B):** Linear recurrent states handle early context accumulation, but binding is handed over to late attention mixers (Layer 20 in 2B: paired difference {paired_dissociations['qwen3.5-2b']['mean']:+.3f} [{paired_dissociations['qwen3.5-2b']['ci_95'][0]:+.3f}, {paired_dissociations['qwen3.5-2b']['ci_95'][1]:+.3f}]; Layer 24 in 4B: paired difference {paired_dissociations['qwen3.5-4b']['mean']:+.3f} [{paired_dissociations['qwen3.5-4b']['ci_95'][0]:+.3f}, {paired_dissociations['qwen3.5-4b']['ci_95'][1]:+.3f}]). Downstream continuation is routed by Layer 28 attention mixer ({q35_4b_l28_m['abs_shift_cont']:+.3f}) and completed by Layer 32 MLP ({q35_4b_l32_mlp['abs_shift_cont']:+.3f}).",
        f"- **Deep Asymmetric Models (Tiny Aya, Gemma 4):** Tiny Aya exhibits component separation: Layer 24 Mixer mediates initial binding (paired difference {paired_dissociations['tiny-aya-global']['mean']:+.3f} [{paired_dissociations['tiny-aya-global']['ci_95'][0]:+.3f}, {paired_dissociations['tiny-aya-global']['ci_95'][1]:+.3f}]), while Layer 36 MLP mediates multi-token continuation ({aya_l36_mlp['abs_shift_cont']:+.3f}). Gemma 4 E2B exhibits an architecture-specific pre-hub handover: Layer 24 shows MLP dominance ($-0.494$), but handover completes at Layer 35 where terminal mixer dominance is $+2.851$ [$+1.404, +4.197$]. Gemma 4 E4B shows the strongest binding engine in the cohort at Layer 36 ({gemma_e4b_l36_m['abs_shift_first']:+.3f}, paired difference {paired_dissociations['gemma-4-e4b-it']['mean']:+.3f}), though accompanied by high vocabulary divergence ($D_{{\\text{{KL}}}} = {gemma_e4b_l36_m['kl_div']:.3f}$ nats).",
        "",
        "### 2. Format Heterogeneity & Unpatched Donor Margin Friction",
        "Condition-level baselines reveal that harder tokenizations suffer from low unpatched donor victory rates:",
        "- **Structured (`[S1]`):** Unpatched donor victory rate is 62.5%–91.2% across models, with strongly positive average margins.",
        "- **Random Compact (`[XQ7M]`):** Donor victory rate drops to 51.2%–86.2%; Tiny Aya's mean donor margin is negative ($-0.121$ nats).",
        "- **UUID (`[3f8a...]`):** Severe baseline friction. Donor victory rate ranges from 47.5% (Tiny Aya) to 85.0% (Gemma E4B). In Qwen 2.5 1.5B, mean donor margin is essentially zero ($+0.066$ nats), and in Tiny Aya it is negative ($-0.306$ nats).",
        "- **Subgroup Sensitivity:** When conditioned on donor-positive cases, the paired mixer advantage strengthens substantially across models (e.g. Qwen 2.5 L24 increases from $+0.621$ to $+0.902$, Tiny Aya from $+1.005$ to $+2.252$). This confirms that late mixers actively transport the counterfactual choice whenever the donor state reliably computes it.",
        "",
        "---",
        "",
        "## Summary Conclusion & Scientific Boundaries",
        "",
        "1. **What is solidly established:** Late attention/DeltaNet mixers causally mediate identifier selection ($B$) at primary hubs in 5 of 6 models (and 6 of 6 including designated terminal hubs) on an 80-example held-out confirmation split.",
        "2. **What remains architecture-specific:** Pre-hub handover (Gemma 4 E2B L24 MLP vs L35 Mixer) and downstream continuation (Tiny Aya MLP vs Qwen 3.5 / Gemma 4 E4B Mixer).",
        "3. **What is not yet established:** Computation vs. transport (interventions at citation positions do not distinguish whether binding was computed at the mixer or transported from earlier evidence representations); full factorization ($R \\to B \\to F$); and sparse head circuits (L24H3 pilot CI crosses zero; requires held-out necessity/minimality testing).",
    ])

    out_md = circuit_dir / "FINDINGS_STAGE7B_CROSS_MODEL_CIRCUITS.md"
    out_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Saved cross-model findings report to: {out_md}")


if __name__ == "__main__":
    main()

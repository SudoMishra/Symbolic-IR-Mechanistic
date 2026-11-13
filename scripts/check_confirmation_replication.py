#!/usr/bin/env python3
"""Check replication of preregistered criteria on the confirmation split."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MODELS = [
    ("qwen2.5-1.5b-instruct", "Pure GQA Transformer (28L)", "confirmation_qwen25_15b_analysis.json", [20, 24]),
    ("qwen3.5-2b", "Hybrid Gated DeltaNet (24L)", "confirmation_qwen35_2b_analysis.json", [16, 20]),
    ("tiny-aya-global", "Deep Asymmetric GQA (36L)", "confirmation_tiny_aya_analysis.json", [24, 36]),
    ("qwen3.5-4b", "Hybrid Gated DeltaNet (32L)", "confirmation_qwen35_4b_analysis.json", [24, 28, 32]),
    ("gemma-4-e2b-it", "Deep Asymmetric GQA (35L)", "confirmation_gemma4_e2b_analysis.json", [24, 35]),
    ("gemma-4-e4b-it", "Deep Asymmetric PLE (42L)", "confirmation_gemma4_e4b_analysis.json", [36, 42]),
]

def main():
    print("=" * 95)
    print("STAGE 7B HIGH-POWER CONFIRMATION SPLIT RESULTS (N=80, 240 cases per model)")
    print("=" * 95)

    for mid, arch, fname, layers in MODELS:
        fpath = ROOT / "results/circuit" / fname
        if not fpath.exists():
            decomp = ROOT / "results/circuit" / fname.replace("_analysis.json", "_decomp.jsonl")
            n_done = 0
            if decomp.exists():
                n_done = sum(1 for line in decomp.read_text(encoding="utf-8").splitlines() if line.strip())
            print(f"\n{mid} ({arch}):")
            print(f"  [IN PROGRESS / QUEUED] Completed: {n_done}/240 cases")
            continue

        data = json.loads(fpath.read_text())
        base = data.get("baseline_swap_shifts", {}).get("first_token", {})
        b_mean = base.get("mean", 0)
        b_ci = [base.get("ci95_low", 0), base.get("ci95_high", 0)]
        print(f"\n{mid} ({arch}) - COMPLETED & ANALYZED (240/240):")
        print(f"  Baseline Direct Swap: ΔFirst = {b_mean:+.3f} [{b_ci[0]:+.3f}, {b_ci[1]:+.3f}]")

        layers_dict = data.get("layers", {})
        for l in layers:
            l_str = str(l)
            ld = layers_dict.get(l_str, {})
            m = ld.get("mixer", {})
            mlp = ld.get("mlp", {})
            mf = m.get("abs_shift_first", {})
            mc = m.get("abs_shift_cont", {})
            mlpf = mlp.get("abs_shift_first", {})
            mlpc = mlp.get("abs_shift_cont", {})

            mf_m = mf.get("mean", 0)
            mf_ci = mf.get("ci_95", [0, 0])
            mf_l, mf_h = mf_ci[0], mf_ci[1]
            mc_m = mc.get("mean", 0)
            mc_ci = mc.get("ci_95", [0, 0])
            mc_l, mc_h = mc_ci[0], mc_ci[1]

            mlpf_m = mlpf.get("mean", 0)
            mlpf_ci = mlpf.get("ci_95", [0, 0])
            mlpf_l, mlpf_h = mlpf_ci[0], mlpf_ci[1]
            mlpc_m = mlpc.get("mean", 0)
            mlpc_ci = mlpc.get("ci_95", [0, 0])
            mlpc_l, mlpc_h = mlpc_ci[0], mlpc_ci[1]

            diff = mf_m - mlpf_m
            sig = "*" if (mf_l > 0 or diff > 0.2) else ""

            print(f"  Layer {l}:")
            print(f"    Mixer: ΔFirst = {mf_m:+.3f} [{mf_l:+.3f}, {mf_h:+.3f}] | ΔCont = {mc_m:+.3f} [{mc_l:+.3f}, {mc_h:+.3f}]")
            print(f"    MLP:   ΔFirst = {mlpf_m:+.3f} [{mlpf_l:+.3f}, {mlpf_h:+.3f}] | ΔCont = {mlpc_m:+.3f} [{mlpc_l:+.3f}, {mlpc_h:+.3f}]")
            print(f"    Dissociation (Mixer - MLP ΔFirst): {diff:+.3f} {sig}")

    print("\n" + "=" * 95)

if __name__ == "__main__":
    main()

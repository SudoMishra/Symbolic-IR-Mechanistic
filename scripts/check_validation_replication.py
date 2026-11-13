#!/usr/bin/env python3
"""Check replication of preregistered criteria on the validation split."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MODEL_FILE_MAP = {
    "qwen2.5-1.5b-instruct": "validation_qwen25_15b_analysis.json",
    "qwen3.5-2b": "validation_qwen35_2b_analysis.json",
    "tiny-aya-global": "validation_tiny_aya_analysis.json",
    "qwen3.5-4b": "validation_qwen35_4b_analysis.json",
    "gemma-4-e2b-it": "validation_gemma4_e2b_analysis.json",
    "gemma-4-e4b-it": "validation_gemma4_e4b_analysis.json",
}

def main():
    prereg_p = ROOT / "results/circuit/circuit_preregistration.json"
    prereg = json.loads(prereg_p.read_text())["candidate_circuits"]

    print("=" * 95)
    print("STAGE 7B CIRCUIT REPLICATION & HELD-OUT VALIDATION CHECK (N=32, 96 cases per model)")
    print("=" * 95)

    for model_id, pdata in prereg.items():
        arch = pdata.get("architecture", "")
        cand_layers = pdata.get("candidate_layers")
        filename = MODEL_FILE_MAP.get(model_id)
        filepath = ROOT / "results/circuit" / filename if filename else None

        print(f"\nModel: {model_id} ({arch})")
        print(f"  Target candidate layers: {cand_layers}")

        if not filepath or not filepath.exists():
            print(f"  [ERROR] File {filename} not found!")
            continue

        data = json.loads(filepath.read_text())
        base = data.get("baseline_swap_shifts", {}).get("first_token", {})
        base_df = base.get("mean", 0)
        base_ci = [base.get("ci95_low", 0), base.get("ci95_high", 0)]
        print(f"  Baseline Direct Swap: ΔFirst = {base_df:+.3f} [{base_ci[0]:+.3f}, {base_ci[1]:+.3f}]")

        layers = data.get("layers", {})
        for l_int in cand_layers:
            l_str = str(l_int)
            l_data = layers.get(l_str, {})
            mixer = l_data.get("mixer", {})
            mlp = l_data.get("mlp", {})
            m_f = mixer.get("abs_shift_first", {})
            m_c = mixer.get("abs_shift_cont", {})
            mlp_f = mlp.get("abs_shift_first", {})
            mlp_c = mlp.get("abs_shift_cont", {})

            mf_mean = m_f.get("mean", 0)
            mf_low = m_f.get("ci95_low", 0)
            mf_high = m_f.get("ci95_high", 0)
            mc_mean = m_c.get("mean", 0)
            recov_m = mixer.get("recov_first_mean", 0)
            kl_m = mixer.get("kl_mean", 0)

            mlpf_mean = mlp_f.get("mean", 0)
            mlpf_low = mlp_f.get("ci95_low", 0)
            mlpf_high = mlp_f.get("ci95_high", 0)
            mlpc_mean = mlp_c.get("mean", 0)
            recov_mlp = mlp.get("recov_first_mean", 0)
            kl_mlp = mlp.get("kl_mean", 0)

            diff_first = mf_mean - mlpf_mean
            sig = "*" if (mf_low > 0 or diff_first > 0.2) else ""

            print(f"    Layer {l_str}:")
            print(f"      Mixer: ΔFirst = {mf_mean:+.3f} [{mf_low:+.3f}, {mf_high:+.3f}] | ΔCont = {mc_mean:+.3f} | Recov = {recov_m:.1f}% | KL = {kl_m:.4f}")
            print(f"      MLP:   ΔFirst = {mlpf_mean:+.3f} [{mlpf_low:+.3f}, {mlpf_high:+.3f}] | ΔCont = {mlpc_mean:+.3f} | Recov = {recov_mlp:.1f}% | KL = {kl_mlp:.4f}")
            print(f"      Dissociation (Mixer - MLP ΔFirst): {diff_first:+.3f} {sig}")

    print("\n" + "=" * 95)

if __name__ == "__main__":
    main()

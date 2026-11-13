#!/usr/bin/env python3
"""Orchestrator for Stage 7B Discovery and Scaled Validation Cohorts.

Sequentially executes and analyzes circuit decomposition across the 6 models:
1. Qwen 2.5 1.5B (Pure GQA Transformer)
2. Qwen 3.5 2B (Hybrid Gated DeltaNet + GQA)
3. Tiny Aya Global (Multilingual Deep Asymmetric GQA)
4. Qwen 3.5 4B (Hybrid Gated DeltaNet + GQA)
5. Gemma 4 E2B (Deep Asymmetric GQA)
6. Gemma 4 E4B (Deep Asymmetric GQA)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

ROOT = Path(__file__).resolve().parent.parent

MODELS = [
    {
        "name": "Qwen 2.5 1.5B",
        "id": "qwen2.5-1.5b-instruct",
        "config": "configs/circuit/circuit_qwen25_15b.yaml",
        "output_decomp": "results/circuit/discovery_qwen25_15b_decomp.jsonl",
        "output_analysis": "results/circuit/discovery_qwen25_15b_analysis.json",
    },
    {
        "name": "Qwen 3.5 2B",
        "id": "qwen3.5-2b",
        "config": "configs/circuit/circuit_qwen35_2b.yaml",
        "output_decomp": "results/circuit/discovery_qwen35_2b_decomp.jsonl",
        "output_analysis": "results/circuit/discovery_qwen35_2b_analysis.json",
    },
    {
        "name": "Tiny Aya Global",
        "id": "tiny-aya-global",
        "config": "configs/circuit/circuit_tiny_aya.yaml",
        "output_decomp": "results/circuit/discovery_tiny_aya_decomp.jsonl",
        "output_analysis": "results/circuit/discovery_tiny_aya_analysis.json",
    },
    {
        "name": "Qwen 3.5 4B",
        "id": "qwen3.5-4b",
        "config": "configs/circuit/circuit_qwen35_4b.yaml",
        "output_decomp": "results/circuit/discovery_qwen35_4b_decomp.jsonl",
        "output_analysis": "results/circuit/discovery_qwen35_4b_analysis.json",
    },
    {
        "name": "Gemma 4 E2B",
        "id": "gemma-4-e2b-it",
        "config": "configs/circuit/circuit_gemma4_e2b.yaml",
        "output_decomp": "results/circuit/discovery_gemma4_e2b_decomp.jsonl",
        "output_analysis": "results/circuit/discovery_gemma4_e2b_analysis.json",
    },
    {
        "name": "Gemma 4 E4B",
        "id": "gemma-4-e4b-it",
        "config": "configs/circuit/circuit_gemma4_e4b.yaml",
        "output_decomp": "results/circuit/discovery_gemma4_e4b_decomp.jsonl",
        "output_analysis": "results/circuit/discovery_gemma4_e4b_analysis.json",
    },
]


def count_completed_lines(file_path: Path) -> int:
    if not file_path.exists():
        return 0
    return sum(1 for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip())


def run_orchestrator(split: str = "discovery", max_cases: int = 96):
    dataset_file = ROOT / f"data/circuit/{split}_n32.jsonl" if split in ("discovery", "validation") else ROOT / "data/circuit/confirmation_n80.jsonl"
    print(f"\n{'='*80}")
    print(f"Stage 7B Cohort Orchestrator: {split.upper()} split ({dataset_file.name})")
    print(f"{'='*80}\n")

    prereg_p = ROOT / "results/circuit/circuit_preregistration.json"
    prereg_data = json.loads(prereg_p.read_text(encoding="utf-8")) if prereg_p.exists() else {}

    for m in MODELS:
        name = m["name"]
        config_p = ROOT / m["config"]
        decomp_p = ROOT / m["output_decomp"]
        analysis_p = ROOT / m["output_analysis"]

        if split != "discovery":
            decomp_p = ROOT / f"results/circuit/{split}_{decomp_p.stem.split('_', 1)[-1]}.jsonl"
            analysis_p = ROOT / f"results/circuit/{split}_{analysis_p.stem.split('_', 1)[-1]}.json"

        completed = count_completed_lines(decomp_p)
        print(f"[{name}] Target: {decomp_p.name} | Completed: {completed}/{max_cases}")

        if completed < max_cases:
            print(f"[{name}] Starting decomposition run...")
            cmd = [
                str(ROOT / ".venv/bin/python"),
                str(ROOT / "scripts/run_circuit_decomposition.py"),
                "--config", str(config_p),
                "--dataset", str(dataset_file),
                "--output", str(decomp_p),
            ]
            if split != "discovery" and prereg_data:
                cand_layers = prereg_data.get("candidate_circuits", {}).get(m["id"], {}).get("candidate_layers")
                if cand_layers:
                    print(f"[{name}] Testing locked candidate circuit layers: {cand_layers}")
                    cmd.extend(["--layers"] + [str(l) for l in cand_layers])
            res = subprocess.run(cmd)
            if res.returncode != 0:
                print(f"[{name}] Run failed with returncode {res.returncode}. Aborting orchestrator.")
                sys.exit(res.returncode)

        # Run analysis
        print(f"[{name}] Running cluster-robust analysis...")
        cmd_ana = [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/analyze_circuit_results.py"),
            "--input", str(decomp_p),
            "--output", str(analysis_p),
        ]
        res_ana = subprocess.run(cmd_ana)
        if res_ana.returncode != 0:
            print(f"[{name}] Analysis failed with returncode {res_ana.returncode}.")
            sys.exit(res_ana.returncode)
        print(f"[{name}] Analysis complete -> {analysis_p.name}\n")

    print("\nAll 6 models successfully completed and analyzed!")


def main():
    parser = argparse.ArgumentParser(description="Stage 7B Cohort Orchestrator")
    parser.add_argument("--split", choices=["discovery", "validation", "confirmation"], default="discovery")
    parser.add_argument("--max-cases", type=int, default=None)
    args = parser.parse_args()

    max_cases = args.max_cases if args.max_cases is not None else (240 if args.split == "confirmation" else 96)
    run_orchestrator(split=args.split, max_cases=max_cases)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Execute Track B: Scaled N >= 500 evaluation across the full 8-model fleet.

Runs:
  1. Stage 1 Citation MVE (N=500) across all 8 models (2,000 reqs / model)
  2. Stage 8 Entity Resolution (N=500) across all 8 models (1,000 reqs / model)
  3. MuSiQue Balanced (N=500) across all 8 models (2,000 reqs / model)
Followed by cross-model synthesis and report generation.
"""

from __future__ import annotations

import gc
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from symbolic_ir.config import load_config
from symbolic_ir.runner import run_experiment
import run_musique_stages

MODELS = [
    "qwen15b",
    "qwen35_2b",
    "qwen35_4b",
    "lfm25_12b",
    "lfm25_26b",
    "gemma4_e2b",
    "gemma4_e4b",
    "tiny_aya",
]


def log(msg: str) -> None:
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


def cleanup() -> None:
    gc.collect()
    time.sleep(1)


def run_scaled_stage1():
    log("=== Track B: Stage 1 Scaled (N=500) ===")
    for model_tag in MODELS:
        config_path = ROOT / f"configs/experiments/citation_mve_500_{model_tag}.yaml"
        log(f"Running Scaled Stage 1 for {model_tag}...")
        config = load_config(config_path)
        out_path, counts = run_experiment(config)
        log(f"Scaled Stage 1 {model_tag} complete: {out_path} ({counts})")

        processed_json = ROOT / f"results/processed/stage1_500_{model_tag}.json"
        findings_md = ROOT / f"FINDINGS_STAGE1_500_{model_tag.upper()}.md"
        subprocess.run([
            sys.executable, str(ROOT / "scripts/analyze_stage1.py"),
            str(out_path),
            "--json-output", str(processed_json),
            "--report-output", str(findings_md)
        ], check=True)
        log(f"Analyzed Scaled Stage 1 {model_tag} -> {processed_json}")
        cleanup()


def run_scaled_stage8():
    log("=== Track B: Stage 8 Scaled Entity Resolution (N=500) ===")
    json_paths = []
    for model_tag in MODELS:
        config_path = ROOT / f"configs/experiments/stage8_pii_500_{model_tag}.yaml"
        log(f"Running Scaled Stage 8 for {model_tag}...")
        config = load_config(config_path)
        out_path, counts = run_experiment(config)
        log(f"Scaled Stage 8 {model_tag} complete: {out_path} ({counts})")

        out_json = ROOT / f"results/processed/stage8_pii_500_{model_tag}.json"
        out_rep = ROOT / f"FINDINGS_STAGE8_500_{model_tag.upper()}.md"
        subprocess.run([
            sys.executable, str(ROOT / "scripts/analyze_stage8.py"),
            "--input", str(out_path),
            "--output-json", str(out_json),
            "--output-report", str(out_rep)
        ], check=True)
        json_paths.append(str(out_json))
        log(f"Processed Scaled Stage 8 {model_tag} -> {out_json}")
        cleanup()

    log("Re-running Stage 8 scaled cross-model analysis...")
    subprocess.run([
        sys.executable, str(ROOT / "scripts/analyze_stage8_cross_model.py"),
        "--inputs", *json_paths,
        "--output", str(ROOT / "FINDINGS_STAGE8_500_CROSS_MODEL.md")
    ], check=True)
    log("Stage 8 scaled cross-model analysis complete.")


def run_scaled_musique():
    log("=== Track B: MuSiQue Scaled (N=500) ===")
    raw_paths = []
    for model_tag in MODELS:
        config_path = ROOT / f"configs/musique/musique_500_{model_tag}.yaml"
        log(f"Running Scaled MuSiQue for {model_tag}...")
        config = load_config(config_path)
        out_path, counts = run_musique_stages.run(config)
        log(f"Scaled MuSiQue {model_tag} complete: {out_path} ({counts})")
        raw_paths.append(out_path)
        cleanup()

    log("Re-running Scaled MuSiQue confirmatory analysis...")
    subprocess.run([
        sys.executable, str(ROOT / "scripts/analyze_musique_confirmatory.py"),
        *raw_paths,
        "--json-output", str(ROOT / "results/processed/musique_500_confirmatory.json"),
        "--report-output", str(ROOT / "FINDINGS_MUSIQUE_500.md")
    ], check=True)
    log("Scaled MuSiQue analysis complete.")


def main():
    log("Starting Track B Scaled Execution (N >= 500) across all 8 models...")
    start_time = time.time()

    # run_scaled_stage1() - Completed 100% across all 8 models
    # run_scaled_stage8() - Completed 100% across all 8 models
    run_scaled_musique()

    elapsed = time.time() - start_time
    log(f"=== Track B Completed Successfully in {elapsed / 60:.1f} minutes ===")


if __name__ == "__main__":
    main()

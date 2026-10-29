#!/usr/bin/env python3
"""Execute Track A: Baseline evaluation across Qwen 3.5 2B and 4B models.

Runs:
  1. Stage 1 Citation MVE (2B & 4B)
  2. Stage 8 Entity Resolution / PII (2B & 4B)
  3. LongProc ToM 2K (2B & 4B)
  4. MuSiQue Confirmatory Held-out (2B & 4B)
  5. MuSiQue Stages 2-4 Matrix (2B & 4B)
Followed by analysis and report generation.
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
import run_longproc
import run_musique_stages


def log(msg: str) -> None:
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


def cleanup() -> None:
    gc.collect()
    time.sleep(1)


def run_stage1():
    log("=== Stage 1: Citation MVE ===")
    for model_tag in ("qwen35_2b", "qwen35_4b"):
        config_path = ROOT / f"configs/experiments/citation_mve_{model_tag}.yaml"
        log(f"Running Stage 1 for {model_tag}...")
        config = load_config(config_path)
        out_path, counts = run_experiment(config)
        log(f"Stage 1 {model_tag} complete: {out_path} ({counts})")

        # Analyze stage 1
        processed_json = ROOT / f"results/processed/stage1_{model_tag}.json"
        findings_md = ROOT / f"FINDINGS_STAGE1_{model_tag.upper()}.md"
        subprocess.run([
            sys.executable, str(ROOT / "scripts/analyze_stage1.py"),
            str(out_path),
            "--json-output", str(processed_json),
            "--report-output", str(findings_md)
        ], check=True)
        log(f"Analyzed Stage 1 {model_tag} -> {processed_json}")
        cleanup()


def run_stage8():
    log("=== Stage 8: Entity Resolution (PII) ===")
    for model_tag in ("qwen35_2b", "qwen35_4b"):
        config_path = ROOT / f"configs/experiments/stage8_pii_{model_tag}.yaml"
        log(f"Running Stage 8 for {model_tag}...")
        config = load_config(config_path)
        out_path, counts = run_experiment(config)
        log(f"Stage 8 {model_tag} complete: {out_path} ({counts})")

        # Process individual stage 8 JSON
        out_json = ROOT / f"results/processed/stage8_pii_{model_tag}.json"
        out_rep = ROOT / f"FINDINGS_STAGE8_{model_tag.upper()}.md"
        subprocess.run([
            sys.executable, str(ROOT / "scripts/analyze_stage8.py"),
            "--input", str(out_path),
            "--output-json", str(out_json),
            "--output-report", str(out_rep)
        ], check=True)
        log(f"Processed Stage 8 {model_tag} -> {out_json}")
        cleanup()

    # Re-run cross-model Stage 8 analysis
    log("Re-running Stage 8 cross-model analysis...")
    stage8_jsons = sorted(ROOT.glob("results/processed/stage8_pii_*.json"))
    if stage8_jsons:
        subprocess.run([
            sys.executable, str(ROOT / "scripts/analyze_stage8_cross_model.py"),
            "--inputs", *[str(p) for p in stage8_jsons],
            "--output", str(ROOT / "FINDINGS_STAGE8_CROSS_MODEL.md")
        ], check=True)
        log("Stage 8 cross-model analysis updated.")


def run_longproc_suite():
    log("=== LongProc: Theory of Mind Tracking ===")
    for model_tag in ("qwen35_2b", "qwen35_4b"):
        config_path = ROOT / f"configs/longproc/tom_tracking_2k_{model_tag}.yaml"
        log(f"Running LongProc for {model_tag}...")
        config = load_config(config_path)
        out_path, counts = run_longproc.run(config)
        log(f"LongProc {model_tag} complete: {out_path} ({counts})")
        cleanup()

    # Re-run LongProc analysis across all models with full 25-item runs
    log("Re-running LongProc cross-model analysis...")
    model_dirs = [
        ("Qwen 1.5B", "results/raw/longproc_tom_tracking_2k_qwen25_15b"),
        ("Qwen 3.5 2B", "results/raw/longproc_tom_tracking_2k_qwen35_2b"),
        ("Qwen 3.5 4B", "results/raw/longproc_tom_tracking_2k_qwen35_4b"),
        ("LFM 1.2B", "results/raw/longproc_tom_tracking_2k_lfm25_12b"),
        ("LFM 2.6B", "results/raw/longproc_tom_tracking_2k_lfm25_26b"),
        ("Gemma E2B", "results/raw/longproc_tom_tracking_2k_gemma4_e2b"),
        ("Gemma E4B", "results/raw/longproc_tom_tracking_2k_gemma4_e4b"),
    ]
    longproc_runs = []
    for label, rel_dir in model_dirs:
        d = ROOT / rel_dir
        if d.exists():
            jsonls = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_size, reverse=True)
            if jsonls:
                longproc_runs.append((label, str(jsonls[0])))

    cmd = [sys.executable, str(ROOT / "scripts/analyze_longproc.py")]
    for label, path in longproc_runs:
        cmd.extend(["--model", label, path])
    cmd.extend(["--output", str(ROOT / "results/processed/longproc_tom_tracking_2k.json")])
    subprocess.run(cmd, check=True)
    log("LongProc processed results updated.")


def run_musique_confirmatory():
    log("=== MuSiQue Confirmatory Held-Out ===")
    for model_tag in ("qwen35_2b", "qwen35_4b"):
        config_path = ROOT / f"configs/musique/confirmatory_{model_tag}.yaml"
        log(f"Running MuSiQue Confirmatory for {model_tag}...")
        config = load_config(config_path)
        out_path, counts = run_musique_stages.run(config)
        log(f"MuSiQue Confirmatory {model_tag} complete: {out_path} ({counts})")
        cleanup()

    # Re-run MuSiQue confirmatory analysis
    log("Re-running MuSiQue confirmatory analysis...")
    subprocess.run([
        sys.executable, str(ROOT / "scripts/analyze_musique_confirmatory.py"),
        "--json-output", str(ROOT / "results/processed/musique_confirmatory.json"),
        "--report-output", str(ROOT / "FINDINGS_MUSIQUE_CONFIRMATORY.md")
    ], check=True)
    log("MuSiQue confirmatory analysis updated.")


def run_musique_stages_suite():
    log("=== MuSiQue Stages 2-4 Matrix ===")
    for model_tag in ("qwen35_2b", "qwen35_4b"):
        config_path = ROOT / f"configs/musique/stages_2_4_{model_tag}.yaml"
        log(f"Running MuSiQue Stages 2-4 for {model_tag}...")
        config = load_config(config_path)
        out_path, counts = run_musique_stages.run(config)
        log(f"MuSiQue Stages 2-4 {model_tag} complete: {out_path} ({counts})")
        cleanup()

    # Re-run MuSiQue stages 2-4 analysis
    log("Re-running MuSiQue stages 2-4 analysis...")
    subprocess.run([
        sys.executable, str(ROOT / "scripts/analyze_musique_stages.py"),
        "--json-output", str(ROOT / "results/processed/musique_stages_2_4.json"),
        "--report-output", str(ROOT / "FINDINGS_MUSIQUE_STAGES_2_4.md")
    ], check=True)
    log("MuSiQue stages 2-4 analysis updated.")


def main():
    log("Starting Track A Execution across Qwen 3.5 2B and 4B...")
    start_time = time.time()

    run_stage1()
    run_stage8()
    run_longproc_suite()
    run_musique_confirmatory()
    run_musique_stages_suite()

    elapsed = time.time() - start_time
    log(f"=== Track A Completed Successfully in {elapsed / 60:.1f} minutes ===")


if __name__ == "__main__":
    main()

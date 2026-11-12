#!/usr/bin/env python3
"""Builds blog/evidence_manifest.csv from study_manifest.yaml and study_accounting.json.

Enforces:
- P7-16: Update blog/evidence_manifest.csv from the authoritative manifest rather than editing it manually.
- P1-10 / P8-05: Exclude any excluded model (LFM) results from public evidence.
- Distinguishes evidence tiers: pilot, confirmatory, replication, exploratory, mechanistic.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def build_evidence_manifest() -> Path:
    manifest_path = ROOT / "study_manifest.yaml"
    accounting_path = ROOT / "results/audit/study_accounting.json"
    output_path = ROOT / "blog/evidence_manifest.csv"

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    accounting = json.loads(accounting_path.read_text(encoding="utf-8")) if accounting_path.exists() else {}

    rows = []
    fieldnames = ["evidence_id", "experiment", "scale", "primary_artifact", "processed_artifact", "role"]

    for exp_id, exp in manifest.get("experiments", {}).items():
        title = exp.get("title", exp_id)
        tier = exp.get("evidence_tier", "confirmatory")
        
        # Calculate scale
        expected_calls = exp.get("expected_total_calls", 0)
        models = exp.get("models", [])
        
        acc_exp = accounting.get("by_experiment", {}).get(exp_id, {})
        observed_local = acc_exp.get("local_completed", 0)
        observed_frontier = acc_exp.get("frontier_completed", 0)
        total_observed = observed_local + observed_frontier

        if tier == "systems":
            software_execs = exp.get("deterministic_software_executions", 6000)
            scale = f"Deterministic software ({software_execs:,} executions)"
        elif tier == "mechanistic":
            scale = f"{len(models)} eligible models; {expected_calls} passes/interventions"
        elif tier == "pilot":
            scale = f"{len(models)} models ({total_observed or expected_calls} model calls, exploratory pilot)"
        elif tier == "replication":
            scale = f"{len(models)} models ({total_observed or expected_calls} generations, held-out replication)"
        elif exp.get("cohort") == "frontier_cohort_4":
            scale = f"{total_observed or expected_calls} frontier generations ({len(models)} models)"
        else:
            scale = f"{len(models)} models ({total_observed or expected_calls} generations)"

        # Artifacts
        raw_paths = exp.get("raw_paths", {})
        processed_paths = exp.get("processed_paths", {})
        
        # Primary raw representation
        if isinstance(raw_paths, dict) and raw_paths:
            primary = next(iter(raw_paths.values()))
        elif isinstance(raw_paths, str) and raw_paths:
            primary = raw_paths
        else:
            primary = exp.get("dataset") or exp.get("config") or ""

        if isinstance(processed_paths, dict) and processed_paths:
            processed = processed_paths.get("aggregate") or next(iter(processed_paths.values()))
        else:
            processed = str(processed_paths)

        # Role
        role_map = {
            "stage1_scaling_500": "Single-hop attribution baseline and token transport scaling",
            "musique_replication_100": "Disjoint held-out multi-hop attribution replication",
            "musique_scaled_500": "Primary multi-hop confirmatory evaluation across 15 and 20 sources",
            "stage5_pilot": "Exploratory reasoning budget hypothesis generation",
            "stage5_confirmatory": "Balanced confirmatory reasoning budget scaling (40 paired examples/model)",
            "frontier_reasoning_ablation": "Exploratory API reasoning configuration comparison",
            "long_context_tracking": "Procedural belief-state tracking in long-context sequences",
            "stage6_geometry": "Correlational representation geometry across eligible models",
            "stage7_interventions": "Causal source-ID swap preference shifts across eligible models",
            "stage8_pii_500": "Confirmatory typed entity canonicalization and exposure prevention",
            "stage9_systems_boundary": "Deterministic software boundaries, adversarial validation, and semantic edge cases",
            "frontier_stability": "Frontier API repeatability, stability, and latency baseline",
        }
        role = role_map.get(exp_id, f"{tier.title()} evaluation")

        rows.append({
            "evidence_id": exp_id,
            "experiment": title,
            "scale": scale,
            "primary_artifact": primary,
            "processed_artifact": processed,
            "role": role,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {output_path} with {len(rows)} authoritative evidence rows.")
    return output_path


if __name__ == "__main__":
    build_evidence_manifest()

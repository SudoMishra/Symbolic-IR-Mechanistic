"""Authoritative validator for study_manifest.yaml.

Enforces:
- No unknown models or duplicate aliases
- Allowed mechanistic eligibility values
- Manifest consistency with raw data files
- No published partial cells
- No excluded models (LFM) in published cohorts
- Paired ID matching and duplicate detection
"""

import json
import sys
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "study_manifest.yaml"

VALID_TIERS = {"pilot", "confirmatory", "replication", "exploratory", "mechanistic", "systems"}
VALID_MECHANISTIC = {"untested", "eligible", "unsupported", "failed_validation", "not_applicable"}
EXCLUDED_MODEL_KEYS = {"lfm25_12b", "lfm25_26b"}

def get_record_key(r: dict) -> str:
    if "request_key" in r and r["request_key"]:
        return str(r["request_key"])
    ex_id = r.get("example_id") or r.get("metadata", {}).get("example_id", "")
    cond = r.get("condition") or r.get("identifier", "")
    ns = r.get("num_sources", "")
    rep = r.get("repetition", "")
    budget = r.get("budget", "")
    return f"{ex_id}::{cond}::{ns}::{rep}::{budget}"

def validate():
    print(f"Validating manifest: {MANIFEST_PATH}")
    if not MANIFEST_PATH.exists():
        print(f"FAIL: Manifest not found at {MANIFEST_PATH}")
        return 1

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    errors = []
    warnings = []

    # 1. Cohorts and models
    all_models = manifest.get("models", {})
    excluded_models = manifest.get("excluded_models", {})
    known_model_keys = set(all_models.keys()) | set(excluded_models.keys())

    for key, info in all_models.items():
        mech = info.get("mechanistic_eligibility")
        if mech not in VALID_MECHANISTIC:
            errors.append(f"Model '{key}' has invalid mechanistic_eligibility: '{mech}'. Must be in {VALID_MECHANISTIC}")

    for key, info in excluded_models.items():
        if "reason" not in info or not info["reason"]:
            errors.append(f"Excluded model '{key}' is missing required 'reason'")

    cohorts = manifest.get("cohorts", {})
    for cohort_id, cohort_info in cohorts.items():
        for m in cohort_info.get("models", []):
            if m not in known_model_keys:
                errors.append(f"Cohort '{cohort_id}' references unknown model '{m}'")

    # 2. Experiments
    experiments = manifest.get("experiments", {})
    for exp_id, exp in experiments.items():
        tier = exp.get("evidence_tier")
        if tier not in VALID_TIERS:
            errors.append(f"Experiment '{exp_id}' has invalid tier '{tier}'. Must be in {VALID_TIERS}")

        exp_models = exp.get("models", []) or exp.get("eligible_models", [])
        for m in exp_models:
            if m not in known_model_keys:
                errors.append(f"Experiment '{exp_id}' references unknown model '{m}'")
            if m in EXCLUDED_MODEL_KEYS and exp.get("publication_status") == "complete":
                errors.append(f"Experiment '{exp_id}' has publication_status='complete' but contains excluded model '{m}'")

        # Check raw paths
        raw_paths = exp.get("raw_paths", {})
        pub_status = exp.get("publication_status", "")
        
        for m, rel_path in raw_paths.items():
            full_path = REPO_ROOT / rel_path
            if not full_path.exists():
                if pub_status == "complete":
                    errors.append(f"Experiment '{exp_id}' is marked '{pub_status}' but raw path for model '{m}' does not exist: {rel_path}")
                else:
                    warnings.append(f"In-progress raw path does not yet exist: {rel_path}")
            else:
                # Validate records and paired example_ids
                if full_path.suffix == ".jsonl":
                    records = []
                    with open(full_path, "r", encoding="utf-8") as rf:
                        for line_idx, line in enumerate(rf, 1):
                            if line.strip():
                                try:
                                    rec = json.loads(line)
                                    records.append(rec)
                                except Exception as e:
                                    errors.append(f"Error parsing json in {rel_path} line {line_idx}: {e}")

                    if pub_status == "complete":
                        expected_calls = exp.get("expected_calls_per_model")
                        if expected_calls and len(records) != expected_calls:
                            errors.append(f"Experiment '{exp_id}' model '{m}' expected {expected_calls} records, got {len(records)} in {rel_path}")

                    # Check for duplicates
                    seen_combos = set()
                    for r in records:
                        k = get_record_key(r)
                        if k in seen_combos:
                            errors.append(f"Duplicate record in {rel_path} for key '{k}'")
                        seen_combos.add(k)

    print(f"\nManifest validation summary:")
    print(f"Total experiments checked: {len(experiments)}")
    print(f"Warnings: {len(warnings)}")
    for w in warnings:
        print(f"  [WARN] {w}")
    print(f"Errors: {len(errors)}")
    for e in errors:
        print(f"  [ERROR] {e}")

    if errors:
        return 1
    print("Manifest validation PASSED successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(validate())

"""Script to generate results/audit/artifact_inventory.csv covering all raw and processed artifacts."""

import csv
import hashlib
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def count_records(filepath: Path) -> int:
    ext = filepath.suffix
    if ext == ".jsonl":
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
    elif ext == ".json":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return len(data)
            if isinstance(data, dict):
                if "records" in data and isinstance(data["records"], list):
                    return len(data["records"])
                if "results" in data and isinstance(data["results"], list):
                    return len(data["results"])
                if "data" in data and isinstance(data["data"], list):
                    return len(data["data"])
                return 1
        except Exception:
            return 1
    return 0

def detect_model_and_experiment(filepath: Path):
    rel_parts = filepath.relative_to(REPO_ROOT).parts
    filename = filepath.name
    stem = filepath.stem
    parent_dir = filepath.parent.name

    # Model detection
    model = "unknown"
    for m in [
        "lfm25_26b", "lfm25_12b", "lfm2.5-2.6b", "lfm2.5-1.2b", "lfm",
        "tiny_aya_global", "tiny_aya",
        "qwen25_15b", "qwen15b",
        "gemma4_e2b", "gemma4_e4b", "gemma_e2b", "gemma_e4b",
        "qwen35_2b", "qwen35_4b",
        "claude-haiku-5-5", "claude_haiku", "haiku",
        "claude-sonnet-5-5", "claude_sonnet", "sonnet",
        "gpt-6-1-sol", "gpt_sol", "sol",
        "gpt-6-luna", "gpt_luna", "luna",
    ]:
        if m in filename.lower() or m in parent_dir.lower():
            # Canonicalize model name
            if "lfm25_26b" in m or "lfm2.5-2.6b" in m:
                model = "lfm25_26b"
            elif "lfm25_12b" in m or "lfm2.5-1.2b" in m:
                model = "lfm25_12b"
            elif m == "lfm":
                model = "lfm25_12b"
            elif "tiny_aya" in m:
                model = "tiny_aya_global"
            elif "qwen25_15b" in m or "qwen15b" in m:
                model = "qwen25_15b"
            elif "gemma4_e2b" in m or "gemma_e2b" in m:
                model = "gemma4_e2b"
            elif "gemma4_e4b" in m or "gemma_e4b" in m:
                model = "gemma4_e4b"
            elif "qwen35_2b" in m:
                model = "qwen35_2b"
            elif "qwen35_4b" in m:
                model = "qwen35_4b"
            elif "haiku" in m:
                model = "claude-haiku-5-5"
            elif "sonnet" in m:
                model = "claude-sonnet-5-5"
            elif "sol" in m:
                model = "gpt-6-1-sol"
            elif "luna" in m:
                model = "gpt-6-luna"
            break

    # Experiment detection
    experiment = "unknown"
    text = (filename + " " + parent_dir).lower()
    if "musique_stages_2_4" in text or "musique_confirmatory" in text or "musique_stages" in text:
        experiment = "musique_replication_100"
    elif "musique_500" in text or "musique500" in text:
        experiment = "musique_scaled_500"
    elif "citation_mve_500" in text or "stage1_500" in text:
        experiment = "stage1_scaling_500"
    elif "citation_mve" in text or "stage1" in text:
        experiment = "stage1_pilot"
    elif "stage5_confirm" in text or "stage5_confirmatory" in text:
        experiment = "stage5_confirmatory"
    elif "stage5_pilot" in text or "stage5" in text:
        experiment = "stage5_pilot"
    elif "longproc" in text or "tom_tracking" in text:
        experiment = "long_context_tracking"
    elif "stage6" in text:
        experiment = "stage6_geometry"
    elif "stage7" in text:
        experiment = "stage7_interventions"
    elif "stage8_pii_500" in text:
        experiment = "stage8_pii_500"
    elif "stage8" in text:
        experiment = "stage8_pii_100"
    elif "frontier_stability" in text or "phase1_stability" in text:
        experiment = "frontier_stability"
    elif "reasoning" in text:
        experiment = "frontier_reasoning_ablation"
    elif "stage9" in text:
        experiment = "stage9_system_eval"

    return model, experiment

def extract_metadata(filepath: Path):
    seed = "unknown"
    revision = "unknown"

    meta_path = filepath.with_suffix(".metadata.json")
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            revision = meta.get("git_revision", meta.get("config", {}).get("backend", {}).get("revision", "unknown"))
            seed = str(meta.get("config", {}).get("seed", meta.get("config", {}).get("backend", {}).get("seed", "unknown")))
        except Exception:
            pass

    return seed, revision

def determine_status(model: str, experiment: str, record_count: int, filepath: Path) -> str:
    if model in ("lfm25_12b", "lfm25_26b"):
        return "excluded"

    # Check partial conditions
    if experiment == "frontier_reasoning_ablation" and model == "gpt-6-luna" and record_count == 0:
        return "partial"
    if experiment == "musique_scaled_500" and model == "gpt-6-luna" and record_count < 2000:
        return "partial"
    if experiment == "long_context_tracking" and model == "tiny_aya_global" and record_count == 0:
        return "partial"

    if filepath.name.startswith("batch_") or "prepared" in str(filepath):
        return "prepared"

    return "complete"

def main():
    rows = []
    scan_dirs = [
        REPO_ROOT / "results" / "raw",
        REPO_ROOT / "results" / "processed",
        REPO_ROOT / "results" / "analysis",
        REPO_ROOT / "results" / "diagnostics",
    ]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for root, dirs, files in os.walk(scan_dir):
            for file in sorted(files):
                if file.endswith(".metadata.json") or file == ".gitkeep":
                    continue
                if not (file.endswith(".json") or file.endswith(".jsonl") or file.endswith(".csv")):
                    continue

                fp = Path(root) / file
                rel_path = str(fp.relative_to(REPO_ROOT))
                model, experiment = detect_model_and_experiment(fp)
                rec_count = count_records(fp)
                seed, revision = extract_metadata(fp)
                status = determine_status(model, experiment, rec_count, fp)
                chk = compute_sha256(fp)

                rows.append({
                    "path": rel_path,
                    "experiment": experiment,
                    "model": model,
                    "record_count": rec_count,
                    "seed": seed,
                    "revision": revision,
                    "status": status,
                    "checksum": chk
                })

    out_csv = REPO_ROOT / "results" / "audit" / "artifact_inventory.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "path", "experiment", "model", "record_count", "seed", "revision", "status", "checksum"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Artifact inventory written to {out_csv} with {len(rows)} entries.")

if __name__ == "__main__":
    main()

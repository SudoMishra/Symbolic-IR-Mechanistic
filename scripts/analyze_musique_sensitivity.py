#!/usr/bin/env python3
"""Comparative analysis of MuSiQue budget sensitivity (256 vs 512 tokens) for LFM2.5-2.6B."""

from __future__ import annotations

import glob
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from symbolic_ir.evaluation.answer import musique_answer_scores


def citation_field(output: str) -> str:
    match = re.search(r"(?im)^\s*CITATIONS?\s*:\s*(.*?)\s*$", output)
    return match.group(1) if match else ""


def relaxed_sources(row: dict) -> set[str]:
    text = citation_field(row["raw_output"])
    found = set()
    for source, label in row["identifier_mapping"]["citation_by_source"].items():
        inner = (
            label[1:-1]
            if len(label) >= 2 and (label[0], label[-1]) in {("[", "]"), ("<", ">")}
            else label
        )
        if label in text or re.search(r"(?<![A-Za-z0-9])" + re.escape(inner) + r"(?![A-Za-z0-9])", text, re.I):
            found.add(source)
    return found


def bootstrap_ci(deltas: list[float], n_boot: int = 2000, alpha: float = 0.05, seed: int = 202601) -> list[float]:
    rng = random.Random(seed)
    n = len(deltas)
    if n == 0:
        return [0.0, 0.0]
    boot_means = []
    for _ in range(n_boot):
        sample = [rng.choice(deltas) for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    lower_idx = int(math.floor(alpha / 2 * n_boot))
    upper_idx = int(math.ceil((1 - alpha / 2) * n_boot)) - 1
    return [round(boot_means[lower_idx], 4), round(boot_means[upper_idx], 4)]


def analyze_run(raw_dir: Path, budget_label: str) -> dict:
    files = list(raw_dir.glob("*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No jsonl found in {raw_dir}")
    records = []
    for f in files:
        with f.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))

    # Group by scenario / num_sources
    by_sources = defaultdict(lambda: {"numeric": {}, "uuid": {}})
    for r in records:
        src = r["dataset_cell"]["num_sources"]
        cond = r["identifier_condition"]
        eg_id = r["example_id"]
        by_sources[src][cond][eg_id] = r

    results = {"budget": budget_label, "scenarios": {}}

    for src in sorted(by_sources):
        numeric_dict = by_sources[src]["numeric"]
        uuid_dict = by_sources[src]["uuid"]

        common_ids = sorted(set(numeric_dict.keys()) & set(uuid_dict.keys()))
        n = len(common_ids)

        num_trunc = sum(1 for eg in common_ids if numeric_dict[eg].get("hit_generation_cap")) / n
        uuid_trunc = sum(1 for eg in common_ids if uuid_dict[eg].get("hit_generation_cap")) / n

        num_recall, uuid_recall = [], []
        num_f1, uuid_f1 = [], []
        for eg in common_ids:
            exp_srcs = set(numeric_dict[eg]["relevant_sources"])
            pred_num = relaxed_sources(numeric_dict[eg])
            pred_uuid = relaxed_sources(uuid_dict[eg])
            num_recall.append(len(pred_num & exp_srcs) / len(exp_srcs) if exp_srcs else 1.0)
            uuid_recall.append(len(pred_uuid & exp_srcs) / len(exp_srcs) if exp_srcs else 1.0)

            _, f1_n = musique_answer_scores(numeric_dict[eg]["parsed_answer"], numeric_dict[eg]["evaluation"]["accepted_answers"])
            _, f1_u = musique_answer_scores(uuid_dict[eg]["parsed_answer"], uuid_dict[eg]["evaluation"]["accepted_answers"])
            num_f1.append(f1_n)
            uuid_f1.append(f1_u)

        recall_deltas = [u - num for u, num in zip(uuid_recall, num_recall)]
        f1_deltas = [u - num for u, num in zip(uuid_f1, num_f1)]

        num_mal = sum(len(numeric_dict[eg]["evaluation"].get("malformed_ids", [])) for eg in common_ids)
        uuid_mal = sum(len(uuid_dict[eg]["evaluation"].get("malformed_ids", [])) for eg in common_ids)

        results["scenarios"][f"{src}_sources"] = {
            "n_pairs": n,
            "numeric_truncation_rate": round(num_trunc, 4),
            "uuid_truncation_rate": round(uuid_trunc, 4),
            "numeric_binding_recall": round(sum(num_recall) / n, 4),
            "uuid_binding_recall": round(sum(uuid_recall) / n, 4),
            "binding_recall_delta": round(sum(recall_deltas) / n, 4),
            "binding_recall_ci_95": bootstrap_ci(recall_deltas),
            "numeric_answer_f1": round(sum(num_f1) / n, 4),
            "uuid_answer_f1": round(sum(uuid_f1) / n, 4),
            "answer_f1_delta": round(sum(f1_deltas) / n, 4),
            "answer_f1_ci_95": bootstrap_ci(f1_deltas),
            "numeric_malformed_count": num_mal,
            "uuid_malformed_count": uuid_mal,
        }
    return results


def main():
    dir_256 = ROOT / "results/raw/musique_confirmatory_lfm25_26b"
    dir_512 = ROOT / "results/raw/musique_sensitivity_lfm25_26b_512"

    res_256 = analyze_run(dir_256, "256_tokens")
    res_512 = analyze_run(dir_512, "512_tokens")

    comparison = {
        "model": "LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m",
        "study": "MuSiQue Budget Sensitivity Analysis (Post-Hoc)",
        "run_256": res_256,
        "run_512": res_512,
    }

    out_file = ROOT / "results/analysis/musique_lfm26b_budget_sensitivity.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    print(f"Saved comparison to {out_file}\n")

    # Print clean Markdown summary table
    print("=" * 105)
    print("MUSIQUE BUDGET SENSITIVITY CHECK: LFM 2.5-2.6B (256 TOKENS vs 512 TOKENS)")
    print("=" * 105)
    print(f"{'Scenario':<14} {'Budget':<12} {'Num Trunc':<11} {'UUID Trunc':<11} {'Num Recall':<12} {'UUID Recall':<12} {'Recall Delta':<14} {'95% Bootstrap CI':<18}")
    print("-" * 105)
    for sc in ["15_sources", "20_sources"]:
        s256 = res_256["scenarios"][sc]
        s512 = res_512["scenarios"][sc]
        print(f"{sc:<14} {'256 tokens':<12} {s256['numeric_truncation_rate']*100:>9.1f}% {s256['uuid_truncation_rate']*100:>9.1f}% {s256['numeric_binding_recall']*100:>10.1f}% {s256['uuid_binding_recall']*100:>10.1f}% {s256['binding_recall_delta']*100:>12.2f} pp {str(s256['binding_recall_ci_95']):<18}")
        print(f"{'':<14} {'512 tokens':<12} {s512['numeric_truncation_rate']*100:>9.1f}% {s512['uuid_truncation_rate']*100:>9.1f}% {s512['numeric_binding_recall']*100:>10.1f}% {s512['uuid_binding_recall']*100:>10.1f}% {s512['binding_recall_delta']*100:>12.2f} pp {str(s512['binding_recall_ci_95']):<18}")
        print("-" * 105)


if __name__ == "__main__":
    main()

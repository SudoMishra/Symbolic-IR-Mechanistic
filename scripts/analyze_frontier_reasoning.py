"""Statistical analysis and reporting for Phase 3 Reasoning Ablation."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.statistics import paired_bootstrap_delta  # noqa: E402


def analyze_reasoning_ablation(
    no_reasoning_file: Path,
    reasoning_file: Path,
) -> dict[str, Any]:
    no_reas_records = [json.loads(line) for line in no_reasoning_file.read_text(encoding="utf-8").splitlines() if line]
    reas_records = [json.loads(line) for line in reasoning_file.read_text(encoding="utf-8").splitlines() if line]

    def index_records(records):
        idx = {}
        for r in records:
            qid = r.get("example_id")
            ns = r.get("num_sources")
            cond = r.get("condition") or r.get("identifier_condition")
            eval_data = r.get("evaluation", {})
            tokens = r.get("token_counts", {})
            idx[(qid, ns, cond)] = {
                "answer_correct": eval_data.get("answer_correct", False),
                "citation_exact_match": eval_data.get("citation_exact_match", False),
                "reasoning_tokens": int(tokens.get("reasoning") or 0),
                "calculated_cost": float(r.get("calculated_cost") or 0.0),
            }
        return idx

    no_idx = index_records(no_reas_records)
    re_idx = index_records(reas_records)

    common_keys = sorted(set(no_idx.keys()) & set(re_idx.keys()))
    if not common_keys:
        return {"error": "No overlapping examples between no-reasoning and reasoning datasets"}

    # Q1: Does reasoning reduce the UUID penalty?
    # Compare (UUID - numeric) in no-reasoning vs reasoning
    common_qids = sorted({k[0] for k in common_keys})
    acc_pen_no = []
    acc_pen_re = []
    cem_pen_no = []
    cem_pen_re = []

    reas_tokens_num = []
    reas_tokens_uuid = []
    costs_no = []
    costs_re = []

    for qid in common_qids:
        for ns in [15, 20]:
            k_num = (qid, ns, "numeric")
            k_uuid = (qid, ns, "uuid")
            if k_num in no_idx and k_uuid in no_idx and k_num in re_idx and k_uuid in re_idx:
                # Delta UUID - numeric for accuracy
                d_acc_no = (1.0 if no_idx[k_uuid]["answer_correct"] else 0.0) - (1.0 if no_idx[k_num]["answer_correct"] else 0.0)
                d_acc_re = (1.0 if re_idx[k_uuid]["answer_correct"] else 0.0) - (1.0 if re_idx[k_num]["answer_correct"] else 0.0)
                acc_pen_no.append(d_acc_no)
                acc_pen_re.append(d_acc_re)

                # Delta UUID - numeric for citation exact match
                d_cem_no = (1.0 if no_idx[k_uuid]["citation_exact_match"] else 0.0) - (1.0 if no_idx[k_num]["citation_exact_match"] else 0.0)
                d_cem_re = (1.0 if re_idx[k_uuid]["citation_exact_match"] else 0.0) - (1.0 if re_idx[k_num]["citation_exact_match"] else 0.0)
                cem_pen_no.append(d_cem_no)
                cem_pen_re.append(d_cem_re)

                reas_tokens_num.append(re_idx[k_num]["reasoning_tokens"])
                reas_tokens_uuid.append(re_idx[k_uuid]["reasoning_tokens"])

                costs_no.append(no_idx[k_num]["calculated_cost"] + no_idx[k_uuid]["calculated_cost"])
                costs_re.append(re_idx[k_num]["calculated_cost"] + re_idx[k_uuid]["calculated_cost"])

    acc_pen_diff_boot = paired_bootstrap_delta(acc_pen_re, acc_pen_no, seed=202620)
    cem_pen_diff_boot = paired_bootstrap_delta(cem_pen_re, cem_pen_no, seed=202620)
    reas_diff_boot = paired_bootstrap_delta([float(x) for x in reas_tokens_uuid], [float(x) for x in reas_tokens_num], seed=202620)

    mean_cost_no = sum(costs_no) / len(costs_no) if costs_no else 0.0
    mean_cost_re = sum(costs_re) / len(costs_re) if costs_re else 0.0

    return {
        "n_paired_cells": len(acc_pen_no),
        "citation_exact_match_penalty": {
            "mean_penalty_no_reasoning": round(sum(cem_pen_no) / len(cem_pen_no) * 100.0, 2) if cem_pen_no else 0.0,
            "mean_penalty_with_reasoning": round(sum(cem_pen_re) / len(cem_pen_re) * 100.0, 2) if cem_pen_re else 0.0,
            "delta_reduction": cem_pen_diff_boot.to_dict(),
        },
        "answer_accuracy_penalty": {
            "mean_penalty_no_reasoning": round(sum(acc_pen_no) / len(acc_pen_no) * 100.0, 2) if acc_pen_no else 0.0,
            "mean_penalty_with_reasoning": round(sum(acc_pen_re) / len(acc_pen_re) * 100.0, 2) if acc_pen_re else 0.0,
            "delta_reduction": acc_pen_diff_boot.to_dict(),
        },
        "q2_uuid_causes_more_reasoning_tokens": {
            "mean_reasoning_tokens_numeric": round(sum(reas_tokens_num) / len(reas_tokens_num), 1) if reas_tokens_num else 0.0,
            "mean_reasoning_tokens_uuid": round(sum(reas_tokens_uuid) / len(reas_tokens_uuid), 1) if reas_tokens_uuid else 0.0,
            "reasoning_token_delta": reas_diff_boot.to_dict(),
        },
        "q4_cost_multiplier": {
            "mean_pair_cost_no_reasoning": round(mean_cost_no, 6),
            "mean_pair_cost_with_reasoning": round(mean_cost_re, 6),
            "multiplier": round(mean_cost_re / mean_cost_no, 2) if mean_cost_no > 0 else 0.0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-reasoning-file", type=str, required=True)
    parser.add_argument("--reasoning-file", type=str, required=True)
    args = parser.parse_args()
    res = analyze_reasoning_ablation(Path(args.no_reasoning_file), Path(args.reasoning_file))
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

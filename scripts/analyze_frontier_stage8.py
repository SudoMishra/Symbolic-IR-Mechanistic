"""Statistical analysis and reporting for Phase 4 Stage 8 Frontier evaluations."""

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


def analyze_stage8_file(file_path: Path) -> dict[str, Any]:
    records = [json.loads(line) for line in file_path.read_text(encoding="utf-8").splitlines() if line]
    by_cond = defaultdict(list)
    by_case = defaultdict(dict)

    for r in records:
        cond = r.get("condition")
        case_id = r.get("example_id")
        eval_data = r.get("evaluation", {})
        tokens = r.get("token_counts", {})

        entry = {
            "example_id": case_id,
            "condition": cond,
            "answer_correct": eval_data.get("answer_correct", False),
            "raw_pii_leakage": eval_data.get("raw_pii_leakage", False),
            "input_tokens": int(tokens.get("input") or 0),
            "output_tokens": int(tokens.get("output") or 0),
            "reasoning_tokens": int(tokens.get("reasoning") or 0),
        }
        by_cond[cond].append(entry)
        by_case[case_id][cond] = entry

    summary: dict[str, Any] = {}
    for cond, items in by_cond.items():
        n = len(items)
        if n == 0:
            continue
        acc = sum(1 for it in items if it["answer_correct"]) / n
        leak = sum(1 for it in items if it["raw_pii_leakage"]) / n
        mean_in = sum(it["input_tokens"] for it in items) / n
        mean_out = sum(it["output_tokens"] for it in items) / n
        mean_reas = sum(it["reasoning_tokens"] for it in items) / n

        summary[cond] = {
            "n": n,
            "accuracy": round(acc * 100.0, 2),
            "raw_pii_leakage_rate": round(leak * 100.0, 2),
            "mean_input_tokens": round(mean_in, 1),
            "mean_output_tokens": round(mean_out, 1),
            "mean_reasoning_tokens": round(mean_reas, 1),
        }

    # Primary endpoint: typed minus untyped accuracy
    common_cases = [case_id for case_id, reps in by_case.items() if "typed" in reps and "untyped" in reps]
    acc_typed = [1.0 if by_case[cid]["typed"]["answer_correct"] else 0.0 for cid in common_cases]
    acc_untyped = [1.0 if by_case[cid]["untyped"]["answer_correct"] else 0.0 for cid in common_cases]

    delta = paired_bootstrap_delta(acc_typed, acc_untyped, seed=202618)

    return {
        "conditions": summary,
        "primary_endpoint_typed_minus_untyped": delta.to_dict(),
        "total_cases": len(common_cases),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True)
    args = parser.parse_args()
    res = analyze_stage8_file(Path(args.file))
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

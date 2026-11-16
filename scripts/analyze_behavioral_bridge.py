#!/usr/bin/env python3
"""Phase 6: Statistical Analysis of Behavioral Bridge Free Generation.

Aggregates free generation metrics across clean baseline, swapped baseline,
and causal subspace intervention with paired cluster bootstrap (B=1,000, clustered by example_id):
1. Factual answer correctness (EM).
2. Citation source correctness (gold vs. counterfactual).
3. Citation precision and recall.
4. Error taxonomy: wrong-source, omitted-citation, spurious-citation.
5. Selective dissociation: answer EM preserved while citation redirected to counterfactual.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.analyze_circuit_results import cluster_bootstrap_mean_ci  # noqa: E402


def analyze_behavioral_bridge(
    eval_file: Path,
    output_json: Path,
    output_md: Path,
) -> dict[str, Any]:
    lines = [json.loads(line) for line in eval_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"No records found in {eval_file}")

    print(f"Analyzing {len(lines)} behavioral generation records from {eval_file.name}...")

    conditions = ["clean_baseline", "swapped_baseline", "subspace_projection"]

    # Metrics tracked: {cond: {metric: list of (example_id, float)}}
    data = defaultdict(lambda: defaultdict(list))
    error_counts = defaultdict(lambda: defaultdict(int))

    # Condition format breakdown: {cond: {format: {metric: list of (example_id, float)}}}
    format_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for row in lines:
        cid = row["example_id"]
        fmt = row["condition"]

        # 1. Clean Baseline
        c_eval = row["clean_baseline"]
        data["clean_baseline"]["answer_em"].append((cid, float(c_eval["answer_em"])))
        data["clean_baseline"]["cites_gold"].append((cid, float(c_eval["cites_gold"])))
        data["clean_baseline"]["citation_precision"].append((cid, float(c_eval["citation_precision"])))
        data["clean_baseline"]["citation_recall"].append((cid, float(c_eval["citation_recall"])))
        data["clean_baseline"]["strict_syntax"].append((cid, float(c_eval["strict_syntax"])))
        error_counts["clean_baseline"][c_eval["error_type"]] += 1

        format_data["clean_baseline"][fmt]["answer_em"].append((cid, float(c_eval["answer_em"])))
        format_data["clean_baseline"][fmt]["cites_gold"].append((cid, float(c_eval["cites_gold"])))

        # 2. Swapped Baseline
        s_eval = row["swapped_baseline"]
        data["swapped_baseline"]["answer_em"].append((cid, float(s_eval["answer_em"])))
        data["swapped_baseline"]["cites_swapped"].append((cid, float(s_eval["cites_gold"])))
        data["swapped_baseline"]["citation_precision"].append((cid, float(s_eval["citation_precision"])))
        data["swapped_baseline"]["citation_recall"].append((cid, float(s_eval["citation_recall"])))
        data["swapped_baseline"]["strict_syntax"].append((cid, float(s_eval["strict_syntax"])))
        error_counts["swapped_baseline"][s_eval["error_type"]] += 1

        format_data["swapped_baseline"][fmt]["answer_em"].append((cid, float(s_eval["answer_em"])))
        format_data["swapped_baseline"][fmt]["cites_swapped"].append((cid, float(s_eval["cites_gold"])))

        # 3. Subspace Projection Intervention
        sub_eval = row.get("interventions", {}).get("subspace_projection")
        if sub_eval:
            data["subspace_projection"]["answer_em"].append((cid, float(sub_eval["answer_em"])))
            data["subspace_projection"]["cites_gold"].append((cid, float(sub_eval["cites_gold"])))
            data["subspace_projection"]["cites_counterfactual"].append((cid, float(sub_eval["cites_counterfactual"])))
            data["subspace_projection"]["citation_precision"].append((cid, float(sub_eval["citation_precision"])))
            data["subspace_projection"]["citation_recall"].append((cid, float(sub_eval["citation_recall"])))
            data["subspace_projection"]["selective_dissociation"].append((cid, float(sub_eval["selective_dissociation"])))
            data["subspace_projection"]["strict_syntax"].append((cid, float(sub_eval["strict_syntax"])))
            error_counts["subspace_projection"][sub_eval["error_type"]] += 1

            format_data["subspace_projection"][fmt]["answer_em"].append((cid, float(sub_eval["answer_em"])))
            format_data["subspace_projection"][fmt]["cites_cf"].append((cid, float(sub_eval["cites_counterfactual"])))
            format_data["subspace_projection"][fmt]["selective_dissoc"].append((cid, float(sub_eval["selective_dissociation"])))

    # Bootstrap summaries
    synthesis = {
        "title": "Phase 6: Behavioral Bridge and Free Generation Synthesis",
        "eval_dataset": eval_file.name,
        "total_cases": len(lines),
        "conditions": {},
        "error_taxonomy": dict(error_counts),
        "format_breakdown": {},
    }

    for cname in ["clean_baseline", "swapped_baseline", "subspace_projection"]:
        c_summary = {}
        for mname, pairs in data[cname].items():
            mean, low, high = cluster_bootstrap_mean_ci(pairs)
            c_summary[mname] = {
                "mean_pct": round(mean * 100.0, 2),
                "ci_95": [round(low * 100.0, 2), round(high * 100.0, 2)],
            }
        synthesis["conditions"][cname] = c_summary

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(synthesis, indent=2), encoding="utf-8")
    print(f"Saved behavioral synthesis JSON to: {output_json}")

    # Generate Markdown findings
    md_lines = [
        "# Phase 6: Behavioral Bridge Free Generation Findings",
        "",
        f"- **Dataset**: `{eval_file.name}` ({len(lines)} cases)",
        f"- **Target Intervention**: Layer 14 `pos_post_evidence` Subspace Projection (Rank 8)",
        "",
        "| Evaluation Condition | Answer EM [95% CI] | Cites Target [95% CI] | Precision [95% CI] | Recall [95% CI] | Selective Dissociation [95% CI] | Strict Syntax [95% CI] |",
        "|---|---|---|---|---|---|---|",
    ]

    # Clean
    c = synthesis["conditions"]["clean_baseline"]
    md_lines.append(
        f"| **Clean Prompt Baseline** | {c['answer_em']['mean_pct']:.1f}% [{c['answer_em']['ci_95'][0]:.1f}%, {c['answer_em']['ci_95'][1]:.1f}%] "
        f"| {c['cites_gold']['mean_pct']:.1f}% [{c['cites_gold']['ci_95'][0]:.1f}%, {c['cites_gold']['ci_95'][1]:.1f}%] "
        f"| {c['citation_precision']['mean_pct']:.1f}% [{c['citation_precision']['ci_95'][0]:.1f}%, {c['citation_precision']['ci_95'][1]:.1f}%] "
        f"| {c['citation_recall']['mean_pct']:.1f}% [{c['citation_recall']['ci_95'][0]:.1f}%, {c['citation_recall']['ci_95'][1]:.1f}%] "
        f"| N/A | {c['strict_syntax']['mean_pct']:.1f}% [{c['strict_syntax']['ci_95'][0]:.1f}%, {c['strict_syntax']['ci_95'][1]:.1f}%] |"
    )

    # Swapped
    s = synthesis["conditions"]["swapped_baseline"]
    md_lines.append(
        f"| **Swapped Prompt Baseline** | {s['answer_em']['mean_pct']:.1f}% [{s['answer_em']['ci_95'][0]:.1f}%, {s['answer_em']['ci_95'][1]:.1f}%] "
        f"| {s['cites_swapped']['mean_pct']:.1f}% [{s['cites_swapped']['ci_95'][0]:.1f}%, {s['cites_swapped']['ci_95'][1]:.1f}%] "
        f"| {s['citation_precision']['mean_pct']:.1f}% [{s['citation_precision']['ci_95'][0]:.1f}%, {s['citation_precision']['ci_95'][1]:.1f}%] "
        f"| {s['citation_recall']['mean_pct']:.1f}% [{s['citation_recall']['ci_95'][0]:.1f}%, {s['citation_recall']['ci_95'][1]:.1f}%] "
        f"| N/A | {s['strict_syntax']['mean_pct']:.1f}% [{s['strict_syntax']['ci_95'][0]:.1f}%, {s['strict_syntax']['ci_95'][1]:.1f}%] |"
    )

    # Subspace Patched
    sub = synthesis["conditions"].get("subspace_projection", {})
    if sub:
        md_lines.append(
            f"| **Subspace Patched (L14 Rank 8)** | {sub['answer_em']['mean_pct']:.1f}% [{sub['answer_em']['ci_95'][0]:.1f}%, {sub['answer_em']['ci_95'][1]:.1f}%] "
            f"| {sub['cites_counterfactual']['mean_pct']:.1f}% [{sub['cites_counterfactual']['ci_95'][0]:.1f}%, {sub['cites_counterfactual']['ci_95'][1]:.1f}%] "
            f"| {sub['citation_precision']['mean_pct']:.1f}% [{sub['citation_precision']['ci_95'][0]:.1f}%, {sub['citation_precision']['ci_95'][1]:.1f}%] "
            f"| {sub['citation_recall']['mean_pct']:.1f}% [{sub['citation_recall']['ci_95'][0]:.1f}%, {sub['citation_recall']['ci_95'][1]:.1f}%] "
            f"| {sub['selective_dissociation']['mean_pct']:.1f}% [{sub['selective_dissociation']['ci_95'][0]:.1f}%, {sub['selective_dissociation']['ci_95'][1]:.1f}%] "
            f"| {sub['strict_syntax']['mean_pct']:.1f}% [{sub['strict_syntax']['ci_95'][0]:.1f}%, {sub['strict_syntax']['ci_95'][1]:.1f}%] |"
        )

    md_lines.extend([
        "",
        "### Error Taxonomy Breakdown",
        "",
        "| Evaluation Condition | Error Free | Counterfactual Cited | Omitted Citation | Wrong Source | Spurious Citation | Answer Incorrect | Both Incorrect |",
        "|---|---|---|---|---|---|---|---|",
    ])

    for cname in ["clean_baseline", "swapped_baseline", "subspace_projection"]:
        errs = error_counts[cname]
        md_lines.append(
            f"| `{cname}` | {errs.get('none', 0)} | {errs.get('counterfactual_cited', 0)} | {errs.get('omitted_citation', 0)} | {errs.get('wrong_source', 0)} | {errs.get('spurious_citation', 0)} | {errs.get('answer_incorrect', 0)} | {errs.get('both_incorrect', 0)} |"
        )

    output_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Saved behavioral findings Markdown to: {output_md}")
    return synthesis


def main():
    parser = argparse.ArgumentParser(description="Phase 6: Analyze Behavioral Bridge Free Generation Results")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    analyze_behavioral_bridge(
        eval_file=Path(args.input),
        output_json=Path(args.output_json),
        output_md=Path(args.output_md),
    )


if __name__ == "__main__":
    main()

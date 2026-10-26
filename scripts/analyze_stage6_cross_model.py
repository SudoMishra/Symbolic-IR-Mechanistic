#!/usr/bin/env python3
"""Build a compact cross-model synthesis from completed Stage 6 JSON reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def effect(result: dict, metric: str) -> dict:
    return result["paired_token_likelihood_effects"]["structured_vs_uuid"][metric]


def point(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def effect_point(metric: dict) -> str:
    low, high = metric["bootstrap_95_ci"]
    return f"{metric['mean']:+.3f} [{low:+.3f}, {high:+.3f}]"


def significant_direction(metric: dict) -> int:
    low, high = metric["bootstrap_95_ci"]
    return 1 if low > 0 else -1 if high < 0 else 0


def report(items: list[tuple[str, dict]]) -> str:
    lines = [
        "# Stage 6 cross-model replication", "",
        "All models use the same 80 semantic examples and three paired identifier formats. States are "
        "teacher-forced and span-aligned; likelihood deltas are UUID minus structured.", "",
        "The operational representation gate requires minimum source-fact CKA ≥0.90, a source-label CKA gain "
        "of at least 0.10 over the embedding layer, and a final-layer question-minus-pre-citation cosine gap "
        "of at least 0.05.", "",
        "| Model | Blocks | Label CKA L0 → peak (layer) | Min fact CKA | Final question / pre-citation / citation cosine | Answer NLL Δ | Citation total NLL Δ | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    answer_positive, citation_positive, citation_negative = [], [], []
    passed = []
    for label, result in items:
        pair = result["cross_condition"]["structured_vs_uuid"]
        gate = result["checkpoint6"]
        label_curve = pair["source_label_cka"]["mean"]
        peak = gate.get("label_cka_peak_layer", max(range(len(label_curve)), key=label_curve.__getitem__))
        minimum_fact_cka = gate.get("minimum_source_fact_cka", min(pair["source_content_cka"]["mean"]))
        answer = effect(result, "uuid_minus_structured_answer_nll")
        citation = effect(result, "uuid_minus_structured_citation_total_nll")
        lines.append(
            f"| {label} | {result['layers'] - 1} | {point(label_curve[0])} → "
            f"{point(label_curve[peak])} (L{peak}) | {point(minimum_fact_cka)} | "
            f"{point(pair['question_cosine']['mean'][-1])} / "
            f"{point(pair['pre_citation_cosine']['mean'][-1])} / "
            f"{point(pair['citation_cosine']['mean'][-1])} | {effect_point(answer)} | "
            f"{effect_point(citation)} | {gate['decision']} |"
        )
        if gate["decision"] == "proceed_to_targeted_stage7":
            passed.append(label)
        if significant_direction(answer) > 0:
            answer_positive.append(label)
        direction = significant_direction(citation)
        if direction > 0:
            citation_positive.append(label)
        elif direction < 0:
            citation_negative.append(label)

    lines.extend((
        "", "## Synthesis", "",
        f"The roadmap's geometric signature passed the automated gate in {len(passed)}/{len(items)} models: "
        f"{', '.join(passed) if passed else 'none'}. Across those models, source-fact geometry remains largely "
        "format-invariant while source-label geometry converges after lexically different embeddings and citation "
        "states become more format-specific late in the stack.", "",
        f"A statistically positive UUID answer-NLL penalty appears in "
        f"{', '.join(answer_positive) if answer_positive else 'no model'}. A positive total citation-NLL penalty "
        f"appears in {', '.join(citation_positive) if citation_positive else 'no model'}, while a negative total "
        f"citation-NLL effect appears in {', '.join(citation_negative) if citation_negative else 'no model'}. "
        "The shared representation pattern alongside heterogeneous likelihood costs argues against one universal "
        "literal-copying explanation; Stage 7 should test whether causal binding interventions transfer across models.", "",
        "## Stage 7 intervention targets", "",
        "| Model | Candidate binding layers | Late output comparison layers |", "|---|---|---|",
    ))
    for label, result in items:
        gate = result["checkpoint6"]
        binding = gate["candidate_binding_layers"]
        output = gate["candidate_output_layers"]
        lines.append(f"| {label} | {binding[0]}–{binding[-1]} | {output[0]}–{output[-1]} |")
    lines.extend((
        "",
        "Tiny Aya is not included because its official Transformers checkpoint is gated and this host is not "
        "authenticated. The local GGUF artifact supports behavioral generation but does not expose per-layer residual "
        "states, so substituting it would not be the same Stage 6 experiment.", "",
    ))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs=2, action="append", metavar=("LABEL", "JSON"), required=True)
    parser.add_argument("--output", default="FINDINGS_STAGE6_CROSS_MODEL.md")
    args = parser.parse_args()
    items = [(label, json.loads(Path(path).read_text())) for label, path in args.input]
    Path(args.output).write_text(report(items), encoding="utf-8")
    print(json.dumps({"models": len(items), "output": args.output}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

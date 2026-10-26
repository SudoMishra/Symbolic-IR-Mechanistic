"""Analyze matched identifier experiments across local model families."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_followups import paired_compare
from analyze_stage1 import cell_summary, enrich, paired_effect


def load(path: str, expected: int) -> list[dict]:
    rows = [
        enrich(json.loads(line))
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(rows) != expected:
        raise ValueError(f"Expected {expected} records in {path}, found {len(rows)}")
    return rows


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def pp(value: float) -> str:
    return f"{100 * value:+.1f} pp"


def analyze_model(label: str, stage1_path: str, numeric_path: str) -> dict:
    stage1 = load(stage1_path, 400)
    numeric = load(numeric_path, 100)
    structured20 = [
        row for row in stage1
        if len(row["source_order"]) == 20 and row["identifier_condition"] == "structured"
    ]
    return {
        "label": label,
        "model": stage1[0]["model"],
        "revision": stage1[0]["model_revision"],
        "stage1_path": stage1_path,
        "numeric_path": numeric_path,
        "cells": [
            cell_summary(stage1, count, condition)
            for count in (5, 20)
            for condition in ("structured", "uuid")
        ],
        "structured_vs_uuid": [
            paired_effect(stage1, count, metric)
            for count in (5, 20)
            for metric in ("answer_content_correct", "citation_strict_correct", "source_binding_exact")
        ],
        "numeric_cell": cell_summary(numeric, 20, "numeric"),
        "numeric_vs_structured": [
            paired_compare(structured20, numeric, "structured", "numeric", metric)
            for metric in ("answer_content", "citation_strict", "source_binding")
        ],
    }


def find_cell(model: dict, sources: int, condition: str) -> dict:
    return next(
        cell for cell in model["cells"]
        if cell["num_sources"] == sources and cell["identifier_condition"] == condition
    )


def find_effect(model: dict, sources: int, metric: str) -> dict:
    return next(
        effect for effect in model["structured_vs_uuid"]
        if effect["num_sources"] == sources and effect["metric"] == metric
    )


def matched_effect(model: dict, metric: str) -> dict:
    return next(effect for effect in model["numeric_vs_structured"] if effect["metric"] == metric)


def report(result: dict) -> str:
    models = result["models"]
    lines = [
        "# Cross-model symbolic-identifier findings",
        "",
        "## Executive result",
        "",
        "The matched experiment was replicated on Qwen2.5-1.5B, LiquidAI LFM2.5-1.2B, and Gemma 4 E2B/E4B. Every model saw the same 100 canonical examples in each condition, with deterministic decoding and native GGUF tokenization.",
        "",
        "The central question is whether compact structured aliases improve exact source binding relative to UUIDs. Literal citation formatting is reported separately because omitted brackets can make strict exact match disagree with successful source selection.",
        "",
        "## Exact source binding",
        "",
        "| Model | 5 src structured | 5 src UUID | UUID−structured | 20 src structured | 20 src UUID | UUID−structured |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model in models:
        s5, u5 = find_cell(model, 5, "structured"), find_cell(model, 5, "uuid")
        s20, u20 = find_cell(model, 20, "structured"), find_cell(model, 20, "uuid")
        e5 = find_effect(model, 5, "source_binding_exact")
        e20 = find_effect(model, 20, "source_binding_exact")
        lines.append(
            f"| {model['label']} | {percent(s5['metrics']['source_binding_exact']['rate'])} | "
            f"{percent(u5['metrics']['source_binding_exact']['rate'])} | {pp(e5['uuid_minus_structured'])} | "
            f"{percent(s20['metrics']['source_binding_exact']['rate'])} | {percent(u20['metrics']['source_binding_exact']['rate'])} | "
            f"{pp(e20['uuid_minus_structured'])} |"
        )
    lines.extend((
        "",
        "## Twenty-source behavior and cost",
        "",
        "| Model | Identifier | Answer content | Citation strict | Exact binding | Input tokens | Output tokens | Latency |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ))
    for model in models:
        for condition in ("structured", "uuid"):
            cell = find_cell(model, 20, condition)
            metrics = cell["metrics"]
            lines.append(
                f"| {model['label']} | {condition} | {percent(metrics['answer_content']['rate'])} | "
                f"{percent(metrics['citation_strict']['rate'])} | {percent(metrics['source_binding_exact']['rate'])} | "
                f"{cell['mean_input_tokens']:.1f} | {cell['mean_output_tokens']:.1f} | {cell['mean_latency_seconds']:.2f}s |"
            )
    lines.extend((
        "",
        "Token counts use each model's native tokenizer, so within-model structured/UUID ratios are the fair comparison; absolute counts across tokenizer families are descriptive.",
        "",
        "## Numeric-alias control at 20 sources",
        "",
        "Numeric `[1]` and structured `[S1]` are paired on the same examples. Effects are numeric minus structured. They are exactly token-matched under Qwen's tokenizer; under LiquidAI and Gemma tokenizers, numeric IDs are one token shorter per identifier (20 fewer prompt tokens in this cell), so those effects combine syntax and length.",
        "",
        "| Model | ID tokens numeric / structured | Input tokens numeric / structured | Numeric binding | Structured binding | Binding delta (95% CI) | Strict delta |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ))
    for model in models:
        numeric = model["numeric_cell"]
        structured = find_cell(model, 20, "structured")
        binding = matched_effect(model, "source_binding")
        strict = matched_effect(model, "citation_strict")
        answer = matched_effect(model, "answer_content")
        low, high = binding["bootstrap_95_ci"]
        lines.append(
            f"| {model['label']} | {numeric['mean_identifier_tokens']:.2f} / {structured['mean_identifier_tokens']:.2f} | "
            f"{numeric['mean_input_tokens']:.1f} / {structured['mean_input_tokens']:.1f} | "
            f"{percent(numeric['metrics']['source_binding_exact']['rate'])} | "
            f"{percent(structured['metrics']['source_binding_exact']['rate'])} | {pp(binding['delta'])} "
            f"([{pp(low)}, {pp(high)}], p={binding['mcnemar_exact_p']:.3g}) | {pp(strict['delta'])} |"
        )
    lines.extend((
        "",
        "## Statistical detail: UUID minus structured binding",
        "",
        "| Model | Sources | Delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |",
        "|---|---:|---:|---:|---:|---:|",
    ))
    for model in models:
        for sources in (5, 20):
            effect = find_effect(model, sources, "source_binding_exact")
            low, high = effect["bootstrap_95_ci"]
            lines.append(
                f"| {model['label']} | {sources} | {pp(effect['uuid_minus_structured'])} | "
                f"[{pp(low)}, {pp(high)}] | {effect['structured_only_correct']} / {effect['uuid_only_correct']} | "
                f"{effect['mcnemar_exact_p']:.3g} |"
            )
    lines.extend((
        "",
        "## Main findings",
        "",
        "1. **The accuracy effect is model-dependent, not universal.** Compact structured aliases beat UUIDs on Qwen and LiquidAI, UUIDs beat structured aliases on Gemma 4 E2B, and Gemma 4 E4B was at ceiling for both.",
        "2. **Compact aliases are universally more efficient in this study.** At 20 sources, UUIDs added 70–94% input tokens and 77–129% latency across the four models.",
        "3. **More capability can erase the accuracy tradeoff.** E4B achieved 100% exact binding in all four Stage-1 cells, leaving efficiency and formatting as the differentiators. This is one checkpoint, not a parameter-scaling law.",
        "4. **Strict citation match can misdiagnose source selection.** Wrapper omissions were common and model-specific; relaxed binding is therefore the primary behavioral metric.",
        "5. **The numeric control does not isolate semantics on three tokenizers.** Qwen's exact token match gave an inconclusive +8 pp binding effect. LiquidAI was also inconclusive. E2B's significant +13 pp numeric effect is jointly attributable to label form and a 20-token prompt reduction; E4B remained at ceiling.",
        "",
        "## Interpretation boundaries",
        "",
        "- These are CPU, quantized-model results: Qwen and LiquidAI use Q4_K_M; the official Gemma 4 artifacts use Q4_0 QAT.",
        "- The models are comparison-scale local models, not identical in parameter count or artifact size; the official Gemma 4 GGUF files are materially larger than the Qwen and LiquidAI files.",
        "- One deterministic seed measures item variation but not decoding-seed or quantization variance.",
        "- The task is fictional, single-hop retrieval with 5 or 20 sources. It does not establish effects for multi-hop reasoning or natural corpora.",
        "- Latency includes prompt prefill plus generation and was measured sequentially on the same CPU runtime.",
        "",
    ))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", action="append", nargs=3, metavar=("LABEL", "STAGE1", "NUMERIC"), required=True,
        help="Repeat for each model: display label, 400-row Stage 1 JSONL, 100-row numeric JSONL.",
    )
    parser.add_argument("--json-output", default="results/processed/cross_model.json")
    parser.add_argument("--report-output", default="FINDINGS_CROSS_MODEL.md")
    args = parser.parse_args()
    result = {"models": [analyze_model(*spec) for spec in args.model]}
    json_path = Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = Path(args.report_output)
    report_path.write_text(report(result), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

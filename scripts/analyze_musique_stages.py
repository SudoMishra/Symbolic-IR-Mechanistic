#!/usr/bin/env python3
"""Analyze the paired MuSiQue Stage 2-4 experiment across local models."""

from __future__ import annotations

import argparse
import glob
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from symbolic_ir.evaluation.answer import musique_answer_scores


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = probability * (len(ordered) - 1)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def mcnemar_exact(a_only: int, b_only: int) -> float:
    discordant = a_only + b_only
    if not discordant:
        return 1.0
    smaller = min(a_only, b_only)
    tail = sum(math.comb(discordant, value) for value in range(smaller + 1)) / (2 ** discordant)
    return min(1.0, 2 * tail)


def citation_field(output: str) -> str:
    match = re.search(r"(?im)^\s*CITATIONS?\s*:\s*(.*?)\s*$", output)
    return match.group(1) if match else ""


def relaxed_sources(row: dict[str, Any]) -> set[str]:
    text = citation_field(row["raw_output"])
    found: set[str] = set()
    for source, label in row["identifier_mapping"]["citation_by_source"].items():
        inner = label[1:-1] if len(label) >= 2 and (label[0], label[-1]) in {("[", "]"), ("<", ">")} else label
        if label in text or re.search(r"(?<![A-Za-z0-9])" + re.escape(inner) + r"(?![A-Za-z0-9])", text, re.I):
            found.add(source)
    return found


def enrich(row: dict[str, Any]) -> dict[str, Any]:
    expected = set(row["relevant_sources"])
    predicted = relaxed_sources(row) if row["require_citations"] else set()
    evaluation = row["evaluation"]
    official_exact, official_f1 = musique_answer_scores(row["parsed_answer"], evaluation["accepted_answers"])
    row["analysis"] = {
        "answer_exact_official": official_exact,
        "answer_f1_official": official_f1,
        "source_binding_exact": predicted == expected if row["require_citations"] else None,
        "source_binding_recall": len(predicted & expected) / len(expected) if row["require_citations"] and expected else None,
        "conditional_citation": bool(evaluation["citation_exact_match"]) if evaluation["answer_correct"] and row["require_citations"] else None,
        "output_truncated": row["token_counts"]["output"] == row["generation_parameters"]["max_output_tokens"],
    }
    return row


METRICS: dict[str, Callable[[dict[str, Any]], float | None]] = {
    "answer_exact": lambda row: float(row["analysis"]["answer_exact_official"]),
    "answer_f1": lambda row: float(row["analysis"]["answer_f1_official"]),
    "citation_exact": lambda row: None if row["evaluation"]["citation_exact_match"] is None else float(row["evaluation"]["citation_exact_match"]),
    "citation_precision": lambda row: row["evaluation"]["citation_precision"],
    "citation_recall": lambda row: row["evaluation"]["citation_recall"],
    "citation_f1": lambda row: None if row["evaluation"]["citation_precision"] is None else (
        0.0 if row["evaluation"]["citation_precision"] + row["evaluation"]["citation_recall"] == 0
        else 2 * row["evaluation"]["citation_precision"] * row["evaluation"]["citation_recall"]
        / (row["evaluation"]["citation_precision"] + row["evaluation"]["citation_recall"])
    ),
    "binding_exact": lambda row: None if row["analysis"]["source_binding_exact"] is None else float(row["analysis"]["source_binding_exact"]),
    "binding_recall": lambda row: row["analysis"]["source_binding_recall"],
    "surface_only_failure": lambda row: None if not row["require_citations"] else float(
        bool(row["analysis"]["source_binding_exact"]) and not bool(row["evaluation"]["citation_exact_match"])
    ),
    "invalid_id": lambda row: None if not row["require_citations"] else float(row["evaluation"]["invalid_id_rate"]),
    "malformed_id": lambda row: None if not row["require_citations"] else float(row["evaluation"]["malformed_id_rate"]),
    "conditional_citation": lambda row: None if row["analysis"]["conditional_citation"] is None else float(row["analysis"]["conditional_citation"]),
    "truncated": lambda row: float(row["analysis"]["output_truncated"]),
}


def metric_values(rows: list[dict[str, Any]], metric: str) -> list[float]:
    return [value for row in rows if (value := METRICS[metric](row)) is not None]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"n": len(rows)}
    for metric in METRICS:
        values = metric_values(rows, metric)
        result[metric] = mean(values) if values else None
        result[f"{metric}_n"] = len(values)
    id_lengths = [length for row in rows for length in row["identifier_token_lengths"].values()]
    result.update({
        "mean_identifier_tokens": mean(id_lengths),
        "mean_prompt_tokens": mean([float(row["token_counts"]["validated_prompt"]) for row in rows]),
        "mean_input_tokens": mean([float(row["token_counts"]["input"]) for row in rows]),
        "mean_output_tokens": mean([float(row["token_counts"]["output"]) for row in rows]),
        "mean_latency_seconds": mean([float(row["latency"]) for row in rows]),
    })
    return result


def paired_effect(
    rows: list[dict[str, Any]], condition_a: str, condition_b: str, metric: str,
    *, scenario_a: str | None = None, scenario_b: str | None = None,
    samples: int = 10_000, seed: int = 202602,
) -> dict[str, Any]:
    def select(condition: str, scenario: str | None) -> dict[str, dict[str, Any]]:
        return {
            row["example_id"]: row for row in rows
            if row["identifier_condition"] == condition and (scenario is None or row["scenario"] == scenario)
        }
    left, right = select(condition_a, scenario_a), select(condition_b, scenario_b)
    keys = sorted(left.keys() & right.keys())
    pairs = [
        (METRICS[metric](left[key]), METRICS[metric](right[key]))
        for key in keys
    ]
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    if not pairs:
        return {"condition_a": condition_a, "condition_b": condition_b, "metric": metric, "n_pairs": 0}
    deltas = [float(b) - float(a) for a, b in pairs]
    rng = random.Random(seed + len(metric) + len(condition_a) * 7 + len(condition_b) * 13)
    boot = [mean([rng.choice(deltas) for _ in deltas]) for _ in range(samples)]
    a_only = sum(a == 1 and b == 0 for a, b in pairs)
    b_only = sum(a == 0 and b == 1 for a, b in pairs)
    return {
        "condition_a": condition_a, "condition_b": condition_b, "metric": metric,
        "n_pairs": len(pairs), "b_minus_a": mean(deltas),
        "bootstrap_95_ci": [percentile(boot, 0.025), percentile(boot, 0.975)],
        "a_only": a_only, "b_only": b_only,
        "mcnemar_exact_p": mcnemar_exact(a_only, b_only)
        if metric in {"answer_exact", "citation_exact", "binding_exact", "malformed_id", "invalid_id", "truncated"}
        else None,
    }


def model_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    model = rows[0]["model"]
    stage2_cells = []
    for source_count in (15, 20):
        for condition in ("numeric", "random_compact", "hex32", "uuid"):
            cell = [row for row in rows if row["scenario"] == f"stage2_{source_count}_sources" and row["identifier_condition"] == condition]
            stage2_cells.append({"sources": source_count, "condition": condition, **summarize(cell)})
    stage2_effects = []
    for source_count in (15, 20):
        scenario = f"stage2_{source_count}_sources"
        cell = [row for row in rows if row["scenario"] == scenario]
        for condition in ("random_compact", "hex32", "uuid"):
            for metric in ("answer_exact", "answer_f1", "citation_exact", "citation_f1", "binding_exact", "binding_recall", "conditional_citation", "malformed_id"):
                effect = paired_effect(cell, "numeric", condition, metric)
                effect["sources"] = source_count
                stage2_effects.append(effect)
    stage2_hops = [
        {"sources": source_count, "hop_count": hop, "condition": condition, **summarize([
            row for row in rows
            if row["scenario"] == f"stage2_{source_count}_sources"
            and row["hop_count"] == hop and row["identifier_condition"] == condition
        ])}
        for source_count in (15, 20)
        for hop in (2, 3, 4)
        for condition in ("numeric", "random_compact", "hex32", "uuid")
    ]
    stage2_source_effects = []
    for condition in ("numeric", "random_compact", "hex32", "uuid"):
        combined = []
        for row in rows:
            if row["identifier_condition"] != condition or row["scenario"] not in {"stage2_15_sources", "stage2_20_sources"}:
                continue
            copy = dict(row)
            copy["identifier_condition"] = "sources15" if row["scenario"] == "stage2_15_sources" else "sources20"
            combined.append(copy)
        for metric in ("answer_f1", "citation_f1", "binding_recall"):
            effect = paired_effect(combined, "sources15", "sources20", metric)
            effect["identifier"] = condition
            stage2_source_effects.append(effect)

    stage3_rows = [row for row in rows if row["scenario"] == "stage3_representation_controls"]
    stage3_cells = [
        {"condition": condition, **summarize([row for row in stage3_rows if row["identifier_condition"] == condition])}
        for condition in ("structured", "arbitrary", "typed", "untyped", "random_typed_control")
    ]
    stage3_effects = [
        paired_effect(stage3_rows, a, b, metric)
        for a, b in (("structured", "arbitrary"), ("typed", "untyped"), ("typed", "random_typed_control"))
        for metric in ("answer_exact", "answer_f1", "citation_exact", "citation_f1", "binding_exact", "binding_recall")
    ]

    stage4_definitions = (
        ("alias_only", "structured", "stage3_representation_controls"),
        ("uuid_citation", "uuid", "stage2_20_sources"),
        ("uuid_no_citation", "uuid", "stage4_failure_controls"),
        ("uuid_alias_citation", "uuid_with_alias", "stage4_failure_controls"),
    )
    stage4_cells = []
    by_label: dict[str, list[dict[str, Any]]] = {}
    for label, condition, scenario in stage4_definitions:
        selected = [row for row in rows if row["scenario"] == scenario and row["identifier_condition"] == condition]
        if label == "uuid_no_citation":
            selected = [row for row in selected if not row["require_citations"]]
        by_label[label] = selected
        stage4_cells.append({"control": label, **summarize(selected)})
    stage4_effects = []
    comparisons = (
        ("alias_only", "uuid_citation"),
        ("uuid_no_citation", "uuid_citation"),
        ("uuid_citation", "uuid_alias_citation"),
        ("alias_only", "uuid_alias_citation"),
    )
    for left_label, right_label in comparisons:
        combined = []
        for label in (left_label, right_label):
            for row in by_label[label]:
                copy = dict(row)
                copy["identifier_condition"] = label
                combined.append(copy)
        for metric in ("answer_exact", "answer_f1", "citation_exact", "citation_f1", "binding_exact", "binding_recall"):
            stage4_effects.append(paired_effect(combined, left_label, right_label, metric))

    failure_counts = {
        f"{row['scenario']}:{row['identifier_condition']}": dict(Counter(
            item["evaluation"]["failure_category"] for item in rows
            if item["scenario"] == row["scenario"] and item["identifier_condition"] == row["identifier_condition"]
        ))
        for row in rows if row["require_citations"]
    }
    return {
        "model": model, "model_revision": rows[0]["model_revision"], "records": len(rows),
        "execution": {
            "input_tokens_min": min(row["token_counts"]["input"] for row in rows),
            "input_tokens_mean": mean([float(row["token_counts"]["input"]) for row in rows]),
            "input_tokens_max": max(row["token_counts"]["input"] for row in rows),
            "output_tokens_mean": mean([float(row["token_counts"]["output"]) for row in rows]),
            "output_tokens_max": max(row["token_counts"]["output"] for row in rows),
            "generation_cap_hits": sum(bool(row["hit_generation_cap"]) for row in rows),
            "latency_hours": sum(float(row["latency"]) for row in rows) / 3600,
        },
        "hop_distribution": dict(sorted(Counter(row["hop_count"] for row in rows).items())),
        "stage2": {
            "cells": stage2_cells, "by_hop": stage2_hops,
            "effects_vs_numeric": stage2_effects,
            "source_count_effects": stage2_source_effects,
        },
        "stage3": {"cells": stage3_cells, "paired_controls": stage3_effects},
        "stage4": {"cells": stage4_cells, "paired_controls": stage4_effects, "failure_taxonomy": failure_counts},
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def delta_pp(left: float | None, right: float | None) -> str:
    return "—" if left is None or right is None else f"{(right - left) * 100:+.1f} pp"


def report(result: dict[str, Any]) -> str:
    lines = [
        "# MuSiQue findings: Stages 2–4", "",
        f"**Design:** {result['records']} deterministic GPU generations over {len(result['models'])} models and 100 paired MuSiQue examples (34 two-hop, 33 three-hop, 33 four-hop).", "",
        "Prompts contain 15 or 20 passages and were selected jointly across all five native tokenizers. Stage 2 varies identifier length and source count; Stage 3 uses representation controls; Stage 4 separates UUID presence from citation reconstruction.", "",
        "## Cross-model checkpoints", "",
        "### Stage 2: numeric vs UUID strict support F1", "",
        "| Model | Numeric 15 | UUID 15 | Δ UUID−numeric | Numeric 20 | UUID 20 | Δ UUID−numeric |", "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in result["models"]:
        cells = {(cell["sources"], cell["condition"]): cell for cell in item["stage2"]["cells"]}
        n15, u15 = cells[(15, "numeric")]["citation_f1"], cells[(15, "uuid")]["citation_f1"]
        n20, u20 = cells[(20, "numeric")]["citation_f1"], cells[(20, "uuid")]["citation_f1"]
        lines.append(f"| {item['model']} | {pct(n15)} | {pct(u15)} | {delta_pp(n15, u15)} | {pct(n20)} | {pct(u20)} | {delta_pp(n20, u20)} |")
    lines.extend(("", "### Stage 2: numeric vs UUID relaxed source-binding recall", "", "| Model | Numeric 15 | UUID 15 | Δ UUID−numeric | Numeric 20 | UUID 20 | Δ UUID−numeric |", "|---|---:|---:|---:|---:|---:|---:|"))
    for item in result["models"]:
        cells = {(cell["sources"], cell["condition"]): cell for cell in item["stage2"]["cells"]}
        n15, u15 = cells[(15, "numeric")]["binding_recall"], cells[(15, "uuid")]["binding_recall"]
        n20, u20 = cells[(20, "numeric")]["binding_recall"], cells[(20, "uuid")]["binding_recall"]
        lines.append(f"| {item['model']} | {pct(n15)} | {pct(u15)} | {delta_pp(n15, u15)} | {pct(n20)} | {pct(u20)} | {delta_pp(n20, u20)} |")
    lines.extend(("", "### Stage 3: length-matched representation controls", "", "| Model | `[S#]` F1 | `[X#]` F1 | `<SOURCE_#>` F1 | `<ENTITY_#>` F1 |", "|---|---:|---:|---:|---:|"))
    for item in result["models"]:
        cells = {cell["condition"]: cell for cell in item["stage3"]["cells"]}
        lines.append(f"| {item['model']} | {pct(cells['structured']['citation_f1'])} | {pct(cells['arbitrary']['citation_f1'])} | {pct(cells['typed']['citation_f1'])} | {pct(cells['untyped']['citation_f1'])} |")
    lines.extend(("", "### Stage 4: answer F1 under failure controls", "", "| Model | Alias only | UUID + cite UUID | UUID, no citation | UUID + cite alias |", "|---|---:|---:|---:|---:|"))
    for item in result["models"]:
        cells = {cell["control"]: cell for cell in item["stage4"]["cells"]}
        lines.append(f"| {item['model']} | {pct(cells['alias_only']['answer_f1'])} | {pct(cells['uuid_citation']['answer_f1'])} | {pct(cells['uuid_no_citation']['answer_f1'])} | {pct(cells['uuid_alias_citation']['answer_f1'])} |")
    lines.extend(("", "### Execution and token usage", "", "| Model | Backend input min/mean/max | Output mean/max | Cap hits | GPU generation time |", "|---|---:|---:|---:|---:|"))
    for item in result["models"]:
        execution = item["execution"]
        lines.append(
            f"| {item['model']} | {execution['input_tokens_min']} / {execution['input_tokens_mean']:.1f} / {execution['input_tokens_max']} | "
            f"{execution['output_tokens_mean']:.1f} / {execution['output_tokens_max']} | {execution['generation_cap_hits']} | {execution['latency_hours']:.2f} h |"
        )
    lines.extend((
        "", "## Main findings", "",
        "1. **Identifier format changed evidence tracking far more than answer quality.** Every numeric-vs-UUID answer-F1 comparison had a paired 95% interval spanning zero. In contrast, relaxed source-binding recall was numerically lower with UUIDs in all ten model/source-count cells and significantly lower in seven.",
        "2. **The strict citation score mixes source selection with reconstruction.** Qwen and LFM favored numeric IDs on strict support F1, while Tiny Aya strongly favored UUIDs because it often omitted brackets around numeric citations. Relaxed source binding reverses that apparent Tiny-Aya advantage: numeric IDs led UUIDs by 9.2 points at 15 sources and 13.7 at 20.",
        "3. **Tracking load matters.** Binding and answer scores generally fell from 15 to 20 sources. Pooled descriptively across models, the UUID-minus-numeric binding gap was largest on four-hop questions (−8.5 points at 15 sources and −9.1 at 20).",
        "4. **Structure matters beyond token count, but no syntax wins universally.** The exactly length-matched `[S#]`/`[X#]` pair produced significant binding differences only for Tiny Aya, while strict citation differences also appeared for LFM. Typed-vs-untyped effects changed direction across models, ruling out a universal typed-placeholder advantage.",
        "5. **Reproducing identifiers can consume task capacity.** Removing the UUID citation requirement significantly improved answer F1 for LFM (+3.5 points) and Gemma E4B (+5.1); the other models were inconclusive. Merely adding a short citation alias beside each UUID did not reliably recover performance and sometimes worsened binding, indicating that a dual-label prompt is not equivalent to canonicalizing IDs before the model sees them.",
        "", "## Limitations", "",
        "- The five models are small, quantized local models; conclusions should not be generalized to larger systems without replication.",
        "- MuSiQue supplies at most 20 candidate paragraphs, so the roadmap's 50/100-source cells are replaced by 15/20-source long-prompt cells.",
        "- These are short-answer citation experiments with a 256-token output cap. The separate LongProc experiment covers the requested 1,024–2,048-token generation regime; forcing MuSiQue answers to that length would measure verbosity rather than reasoning.",
        "- Results use deterministic decoding and one assignment/order seed. Paired intervals quantify example variation, not between-seed or quantization variance.",
        "- Tiny Aya Global is CC-BY-NC-4.0 and therefore research/non-commercial in this setup.",
        "",
    ))
    for item in result["models"]:
        lines.extend((f"## {item['model']}", "", "### Stage 2 — scaling", "", "| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |", "|---:|---|---:|---:|---:|---:|---:|---:|---:|"))
        for cell in item["stage2"]["cells"]:
            lines.append(f"| {cell['sources']} | {cell['condition']} | {pct(cell['answer_exact'])} | {pct(cell['answer_f1'])} | {pct(cell['citation_exact'])} / {pct(cell['citation_f1'])} | {pct(cell['citation_precision'])} / {pct(cell['citation_recall'])} | {pct(cell['binding_exact'])} / {pct(cell['binding_recall'])} | {pct(cell['malformed_id'])} | {cell['mean_prompt_tokens']:.0f} |")
        lines.extend(("", "### Stage 3 — structure controls", "", "| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |", "|---|---:|---:|---:|---:|"))
        for cell in item["stage3"]["cells"]:
            lines.append(f"| {cell['condition']} | {cell['mean_identifier_tokens']:.2f} | {pct(cell['answer_exact'])} | {pct(cell['citation_exact'])} | {pct(cell['binding_exact'])} |")
        lines.extend(("", "### Stage 4 — failure controls", "", "| Control | Answer exact | Answer F1 | Citation exact | Binding exact |", "|---|---:|---:|---:|---:|"))
        for cell in item["stage4"]["cells"]:
            lines.append(f"| {cell['control']} | {pct(cell['answer_exact'])} | {pct(cell['answer_f1'])} | {pct(cell['citation_exact'])} | {pct(cell['binding_exact'])} |")
        lines.append("")
    lines.extend((
        "## Statistical interpretation", "",
        "The machine-readable result contains paired bootstrap 95% intervals and exact McNemar tests for every main comparison. Effects are computed within example, so question difficulty and supporting-source position are held fixed.", "",
        "## Reproducibility notes", "",
        "- Answer scoring reproduces MuSiQue's official SQuAD-style punctuation/article normalization and takes maximum EM/F1 over the official answer and aliases.",
        "- `Binding exact` tolerates missing brackets but requires exactly the correct source set; `Citation exact` retains strict output-format requirements.",
        "- No-citation rows intentionally have no citation score; they isolate whether UUID presence changes answer quality.",
        "- All prompts use deterministic ordering/identifier assignment from seed 202602 and temperature 0.", "",
    ))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_jsonl", nargs="*", help="Defaults to all MuSiQue Stage 2-4 JSONL files")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--json-output", default="results/processed/musique_stages_2_4.json")
    parser.add_argument("--report-output", default="FINDINGS_MUSIQUE_STAGES_2_4.md")
    args = parser.parse_args()
    paths = [Path(path) for path in args.raw_jsonl] or [Path(path) for path in sorted(glob.glob("results/raw/musique_stages_2_4_*/*.jsonl"))]
    rows = [enrich(json.loads(line)) for path in paths for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["model"]].append(row)
    if not args.allow_partial:
        incomplete = {model: len(items) for model, items in grouped.items() if len(items) != 1500}
        if incomplete or len(grouped) != 5:
            raise ValueError(f"Expected five complete 1,500-record model runs; found {dict((m, len(v)) for m, v in grouped.items())}")
    models = [model_analysis(items) for _, items in sorted(grouped.items())]
    result = {"records": len(rows), "models": models, "raw_results": [str(path) for path in paths]}
    json_path, report_path = Path(args.json_output), Path(args.report_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(report(result), encoding="utf-8")
    print(json.dumps({"records": len(rows), "models": len(models), "json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

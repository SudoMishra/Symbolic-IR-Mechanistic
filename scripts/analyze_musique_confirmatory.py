#!/usr/bin/env python3
"""Analyze the independent held-out MuSiQue replication."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_musique_stages import enrich, paired_effect, summarize  # noqa: E402


def analyze_model(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cells, effects = [], []
    for sources in (15, 20):
        scenario = f"confirmatory_{sources}_sources"
        subset = [row for row in rows if row["scenario"] == scenario]
        for condition in ("numeric", "uuid"):
            cells.append({"sources": sources, "condition": condition,
                          **summarize([row for row in subset if row["identifier_condition"] == condition])})
        for metric in ("binding_recall", "answer_f1", "citation_f1", "malformed_id", "invalid_id"):
            effect = paired_effect(subset, "numeric", "uuid", metric, seed=202603)
            effect["sources"] = sources
            effects.append(effect)
    return {
        "model": rows[0]["model"], "model_revision": rows[0]["model_revision"],
        "records": len(rows), "cells": cells, "effects": effects,
        "latency_hours": sum(float(row["latency"]) for row in rows) / 3600,
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.1f}%"


def pp(effect: dict[str, Any]) -> str:
    value = effect.get("b_minus_a")
    interval = effect.get("bootstrap_95_ci")
    if value is None or interval is None:
        return "—"
    return f"{100 * value:+.1f} pp [{100 * interval[0]:+.1f}, {100 * interval[1]:+.1f}]"


def report(result: dict[str, Any]) -> str:
    lines = [
        "# Held-out MuSiQue confirmatory replication", "",
        f"**Design:** {result['records']} deterministic GPU generations across {len(result['models'])} models, "
        "using 100 MuSiQue dev examples disjoint from the original 100-example cohort. Each example is paired "
        "across numeric and UUID identifiers at 15 and 20 sources.", "",
        "Primary outcomes are relaxed source-binding recall, official answer F1, strict citation F1, and malformed/invalid identifier rates.", "",
        "## Primary results", "",
        "| Model | Sources | Numeric binding | UUID binding | UUID−numeric binding (95% CI) | Numeric answer F1 | UUID answer F1 | Strict citation F1 Δ | Malformed Δ | Invalid Δ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    negative = 0
    significant_negative = 0
    total_cells = sum(2 for _ in result["models"])
    for model in result["models"]:
        cells = {(cell["sources"], cell["condition"]): cell for cell in model["cells"]}
        effects = {(effect["sources"], effect["metric"]): effect for effect in model["effects"]}
        for sources in (15, 20):
            numeric, uuid = cells[(sources, "numeric")], cells[(sources, "uuid")]
            binding = effects[(sources, "binding_recall")]
            if binding.get("b_minus_a", 0) < 0:
                negative += 1
            if binding.get("bootstrap_95_ci", [0, 0])[1] < 0:
                significant_negative += 1
            lines.append(
                f"| {model['model']} | {sources} | {pct(numeric['binding_recall'])} | {pct(uuid['binding_recall'])} | {pp(binding)} | "
                f"{pct(numeric['answer_f1'])} | {pct(uuid['answer_f1'])} | {pp(effects[(sources, 'citation_f1')])} | "
                f"{pp(effects[(sources, 'malformed_id')])} | {pp(effects[(sources, 'invalid_id')])} |"
            )
    lines.extend((
        "", "## Replication verdict", "",
        f"UUID binding recall was lower in **{negative}/{total_cells}** model/source-count cells; "
        f"**{significant_negative}/{total_cells}** paired bootstrap intervals excluded zero in the negative direction.",
        "", "Answer F1 and strict citation changes should be interpreted separately: answer F1 tests task solution, "
        "while strict citation F1 also penalizes identifier reconstruction and formatting.",
        "", "## Reproducibility", "",
        "- Cohort seed: 202603; 34 two-hop, 33 three-hop, and 33 four-hop questions.",
        "- Prompts were jointly screened with all five native GGUF tokenizers and kept within 2,000–3,700 tokens.",
        "- Temperature 0, 256-token generation cap, full CUDA offload, Q4 quantization.",
        "- Paired effects are UUID minus numeric on the same examples and source ordering; intervals use 10,000 bootstrap samples.", "",
    ))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_jsonl", nargs="*")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--json-output", default="results/processed/musique_confirmatory.json")
    parser.add_argument("--report-output", default="FINDINGS_MUSIQUE_CONFIRMATORY.md")
    args = parser.parse_args()
    paths = [Path(path) for path in args.raw_jsonl] or [
        Path(path) for path in sorted(glob.glob("results/raw/musique_confirmatory_*/*.jsonl"))
    ]
    rows = [enrich(json.loads(line)) for path in paths
            for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["model"]].append(row)
    if not args.allow_partial:
        if len(grouped) < 5 or any(len(items) != 400 for items in grouped.values()):
            raise ValueError(f"Expected at least five complete 400-record runs; found {dict((k, len(v)) for k, v in grouped.items())}")
    models = [analyze_model(items) for _, items in sorted(grouped.items())]
    result = {"records": len(rows), "models": models, "raw_results": [str(path) for path in paths]}
    json_path, report_path = Path(args.json_output), Path(args.report_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(report(result), encoding="utf-8")
    print(json.dumps({"records": len(rows), "models": len(models), "json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

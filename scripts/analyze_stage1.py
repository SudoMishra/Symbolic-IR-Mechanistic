"""Re-score Stage 1 with strict formatting and relaxed source-binding metrics."""

from __future__ import annotations

import argparse
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^\w.%-]+", " ", text.casefold()).split())


def answer_content_correct(row: dict) -> bool:
    expected = normalize(row["evaluation"]["expected_answer"])
    predicted = normalize(row["parsed_answer"])
    return bool(expected) and expected in predicted


def citation_field(output: str) -> str:
    clean = output.strip()
    if "</think>" in clean:
        post = clean.split("</think>")[-1].strip()
        if post:
            clean = post
    m = re.search(r"(?i)\bCITATIONS?\s*:\s*(.*)", clean)
    if not m:
        return ""
    rest = m.group(1)
    m_ans = re.search(r"(?i)\bANSWER\s*:", rest)
    if m_ans:
        rest = rest[:m_ans.start()]
    return rest.strip()


def relaxed_sources(row: dict) -> set[str]:
    text = citation_field(row["raw_output"])
    found = set()
    for source, label in row["identifier_mapping"]["citation_by_source"].items():
        inner = label[1:-1] if (label.startswith("[") and label.endswith("]")) or (label.startswith("<") and label.endswith(">")) else label
        boundary_match = re.search(r"(?<![A-Za-z0-9])" + re.escape(inner) + r"(?![A-Za-z0-9])", text, re.IGNORECASE)
        if label in text or boundary_match:
            found.add(source)
    return found


def enrich(row: dict) -> dict:
    expected = set(row["relevant_sources"])
    predicted = relaxed_sources(row)
    strict = bool(row["evaluation"]["citation_exact_match"])
    strict_fmt = bool(row["evaluation"].get("strict_format", False))
    return {
        **row,
        "rescored": {
            "answer_content_correct": answer_content_correct(row),
            "citation_strict_correct": strict,
            "strict_format_compliant": strict_fmt,
            "source_binding_exact": predicted == expected,
            "source_binding_recall": len(predicted & expected) / len(expected) if expected else 1.0,
            "wrapper_or_surface_failure": predicted == expected and not strict,
            "output_truncated": row["token_counts"].get("output") == row["generation_parameters"]["max_output_tokens"],
        },
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    half = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return center - half, center + half


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = probability * (len(ordered) - 1)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def mcnemar_exact(left_only: int, right_only: int) -> float:
    discordant = left_only + right_only
    if not discordant:
        return 1.0
    smaller = min(left_only, right_only)
    one_tail = sum(math.comb(discordant, value) for value in range(smaller + 1)) / (2 ** discordant)
    return min(1.0, 2 * one_tail)


def paired_effect(rows: list[dict], num_sources: int, metric: str, *, samples: int = 20_000, seed: int = 202601) -> dict:
    by_condition = {
        condition: {row["example_id"]: row for row in rows if len(row["source_order"]) == num_sources and row["identifier_condition"] == condition}
        for condition in ("structured", "uuid")
    }
    keys = sorted(by_condition["structured"].keys() & by_condition["uuid"].keys())
    def value(row: dict) -> float:
        if metric == "answer_exact":
            return float(row["evaluation"]["answer_correct"])
        return float(row["rescored"][metric])
    deltas = [value(by_condition["uuid"][key]) - value(by_condition["structured"][key]) for key in keys]
    structured_only = sum(value(by_condition["structured"][key]) == 1 and value(by_condition["uuid"][key]) == 0 for key in keys)
    uuid_only = sum(value(by_condition["structured"][key]) == 0 and value(by_condition["uuid"][key]) == 1 for key in keys)
    rng = random.Random(seed + num_sources + len(metric))
    bootstrap = [mean([rng.choice(deltas) for _ in deltas]) for _ in range(samples)]
    return {
        "num_sources": num_sources,
        "metric": metric,
        "n_pairs": len(keys),
        "uuid_minus_structured": mean(deltas),
        "bootstrap_95_ci": [percentile(bootstrap, 0.025), percentile(bootstrap, 0.975)],
        "structured_only_correct": structured_only,
        "uuid_only_correct": uuid_only,
        "mcnemar_exact_p": mcnemar_exact(structured_only, uuid_only),
    }


def cell_summary(rows: list[dict], num_sources: int, condition: str) -> dict:
    cell = [row for row in rows if len(row["source_order"]) == num_sources and row["identifier_condition"] == condition]
    binary_metrics = {
        "answer_exact": [bool(row["evaluation"]["answer_correct"]) for row in cell],
        "answer_content": [bool(row["rescored"]["answer_content_correct"]) for row in cell],
        "citation_strict": [bool(row["rescored"]["citation_strict_correct"]) for row in cell],
        "source_binding_exact": [bool(row["rescored"]["source_binding_exact"]) for row in cell],
        "wrapper_or_surface_failure": [bool(row["rescored"]["wrapper_or_surface_failure"]) for row in cell],
        "output_truncated": [bool(row["rescored"]["output_truncated"]) for row in cell],
    }
    metrics = {}
    for name, values in binary_metrics.items():
        successes = sum(values)
        metrics[name] = {"rate": successes / len(values), "wilson_95_ci": list(wilson(successes, len(values))), "count": successes}
    id_lengths = [length for row in cell for length in row["identifier_token_lengths"].values()]
    return {
        "num_sources": num_sources,
        "identifier_condition": condition,
        "n": len(cell),
        "metrics": metrics,
        "mean_source_binding_recall": mean([row["rescored"]["source_binding_recall"] for row in cell]),
        "mean_identifier_tokens": mean(id_lengths),
        "mean_input_tokens": mean([row["token_counts"]["input"] for row in cell]),
        "mean_output_tokens": mean([row["token_counts"]["output"] for row in cell]),
        "mean_latency_seconds": mean([row["latency"] for row in cell]),
    }


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def report_markdown(result: dict) -> str:
    cells = result["cells"]
    lines = [
        "# Stage 1 findings: structured aliases vs UUIDs",
        "",
        f"**Model:** {result['model']}  ",
        f"**Revision:** `{result['model_revision']}`  ",
        f"**Design:** {result['records']} deterministic generations; {result['records'] // 4} paired examples per condition at 5 and 20 sources.",
        "",
        "## Accuracy and binding",
        "",
        "| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for cell in cells:
        m = cell["metrics"]
        lines.append(
            f"| {cell['num_sources']} | {cell['identifier_condition']} | {percent(m['answer_exact']['rate'])} | "
            f"{percent(m['answer_content']['rate'])} | {percent(m['citation_strict']['rate'])} | "
            f"{percent(m['source_binding_exact']['rate'])} | {percent(cell['mean_source_binding_recall'])} |"
        )
    lines.extend((
        "",
        "`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.",
        "",
        "## Efficiency",
        "",
        "| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ))
    for cell in cells:
        lines.append(
            f"| {cell['num_sources']} | {cell['identifier_condition']} | {cell['mean_identifier_tokens']:.2f} | "
            f"{cell['mean_input_tokens']:.2f} | {cell['mean_output_tokens']:.2f} | {cell['mean_latency_seconds']:.2f} | "
            f"{percent(cell['metrics']['wrapper_or_surface_failure']['rate'])} |"
        )
    lines.extend(("", "## Paired effects", "", "Effects are UUID minus structured; negative values favor structured aliases for accuracy.", "", "| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |", "|---:|---|---:|---:|---:|---:|"))
    for effect in result["paired_effects"]:
        low, high = effect["bootstrap_95_ci"]
        lines.append(
            f"| {effect['num_sources']} | {effect['metric']} | {effect['uuid_minus_structured'] * 100:+.1f} pp | "
            f"[{low * 100:+.1f}, {high * 100:+.1f}] pp | {effect['structured_only_correct']} / {effect['uuid_only_correct']} | "
            f"{effect['mcnemar_exact_p']:.3g} |"
        )
    # Extract metrics for narrative
    cell_map = {(c["num_sources"], c["identifier_condition"]): c for c in cells}
    b5_str = cell_map.get((5, "structured"), {}).get("metrics", {}).get("source_binding_exact", {}).get("rate", 0)
    b5_u = cell_map.get((5, "uuid"), {}).get("metrics", {}).get("source_binding_exact", {}).get("rate", 0)
    b20_str = cell_map.get((20, "structured"), {}).get("metrics", {}).get("source_binding_exact", {}).get("rate", 0)
    b20_u = cell_map.get((20, "uuid"), {}).get("metrics", {}).get("source_binding_exact", {}).get("rate", 0)

    s5_str = cell_map.get((5, "structured"), {}).get("metrics", {}).get("citation_strict", {}).get("rate", 0)
    s5_u = cell_map.get((5, "uuid"), {}).get("metrics", {}).get("citation_strict", {}).get("rate", 0)
    s20_str = cell_map.get((20, "structured"), {}).get("metrics", {}).get("citation_strict", {}).get("rate", 0)
    s20_u = cell_map.get((20, "uuid"), {}).get("metrics", {}).get("citation_strict", {}).get("rate", 0)

    ans5_str = cell_map.get((5, "structured"), {}).get("metrics", {}).get("answer_content", {}).get("rate", 0)
    ans5_u = cell_map.get((5, "uuid"), {}).get("metrics", {}).get("answer_content", {}).get("rate", 0)
    ans20_str = cell_map.get((20, "structured"), {}).get("metrics", {}).get("answer_content", {}).get("rate", 0)
    ans20_u = cell_map.get((20, "uuid"), {}).get("metrics", {}).get("answer_content", {}).get("rate", 0)

    in5_str = cell_map.get((5, "structured"), {}).get("mean_input_tokens", 1)
    in5_u = cell_map.get((5, "uuid"), {}).get("mean_input_tokens", 1)
    in20_str = cell_map.get((20, "structured"), {}).get("mean_input_tokens", 1)
    in20_u = cell_map.get((20, "uuid"), {}).get("mean_input_tokens", 1)
    tax5 = ((in5_u - in5_str) / in5_str * 100) if in5_str else 0
    tax20 = ((in20_u - in20_str) / in20_str * 100) if in20_str else 0

    lines.extend((
        "",
        "## Findings",
        "",
        f"1. **Exact source binding:** Exact binding was {percent(b5_str)} vs {percent(b5_u)} at 5 sources, and {percent(b20_str)} vs {percent(b20_u)} at 20 sources (structured vs UUID).",
        f"2. **Strict citation syntax:** Strict syntax compliance was {percent(s5_str)} vs {percent(s5_u)} at 5 sources, and {percent(s20_str)} vs {percent(s20_u)} at 20 sources.",
        f"3. **Answer content invariance:** Answer content accuracy was {percent(ans5_str)} vs {percent(ans5_u)} at 5 sources, and {percent(ans20_str)} vs {percent(ans20_u)} at 20 sources.",
        f"4. **Input token overhead:** UUID prompts imposed a token overhead of +{tax5:.1f}% at 5 sources and +{tax20:.1f}% at 20 sources.",
        "5. **Representation and scale sensitivity:** Performance differences reflect model architecture, capacity, and surface formatting adherence.",
        "",
        "## Limitations",
        "",
        f"- Evaluated on {result['model']} (revision `{result['model_revision']}`); results reflect this specific checkpoint and quantization.",
        "- Evaluated with deterministic decoding (temperature 0) under fixed seed.",
        "- Single-hop fictional QA only; multi-hop tracking is evaluated separately in MuSiQue.",
        "- Output budget was fixed across conditions; truncation is reported per cell.",
        "",
    ))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_jsonl")
    parser.add_argument("--json-output", default="results/processed/stage1_qwen15b.json")
    parser.add_argument("--report-output", default="FINDINGS_STAGE1.md")
    args = parser.parse_args()
    raw_path = Path(args.raw_jsonl)
    rows = [enrich(json.loads(line)) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) < 400 or len(rows) % 4 != 0:
        raise ValueError(f"Expected balanced run (>= 400 records divisible by 4), found {len(rows)}")
    result = {
        "raw_results": str(raw_path),
        "records": len(rows),
        "model": rows[0]["model"],
        "model_revision": rows[0]["model_revision"],
        "cells": [cell_summary(rows, count, condition) for count in (5, 20) for condition in ("structured", "uuid")],
        "paired_effects": [
            paired_effect(rows, count, metric)
            for count in (5, 20)
            for metric in ("answer_exact", "answer_content_correct", "citation_strict_correct", "source_binding_exact")
        ],
    }
    json_path = Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = Path(args.report_output)
    report_path.write_text(report_markdown(result), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

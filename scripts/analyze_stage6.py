#!/usr/bin/env python3
"""Analyze paired Stage 6 hidden-state representations."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


CONDITIONS = ("structured", "random_compact", "uuid")
PAIRS = (("structured", "random_compact"), ("structured", "uuid"), ("random_compact", "uuid"))
VECTOR_FIELDS = ("question", "pre_answer", "answer", "pre_citation", "citation")
BOOTSTRAPS = 5_000


def cosine(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left = left.astype(np.float32)
    right = right.astype(np.float32)
    numerator = np.sum(left * right, axis=-1)
    denominator = np.linalg.norm(left, axis=-1) * np.linalg.norm(right, axis=-1)
    return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator != 0)


def alignment_margin(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left = left.astype(np.float32)
    right = right.astype(np.float32)
    left /= np.maximum(np.linalg.norm(left, axis=-1, keepdims=True), 1e-12)
    right /= np.maximum(np.linalg.norm(right, axis=-1, keepdims=True), 1e-12)
    matrix = np.einsum("lnd,lmd->lnm", left, right)
    diagonal = np.diagonal(matrix, axis1=1, axis2=2).mean(axis=1)
    count = matrix.shape[1]
    off_diagonal = (matrix.sum(axis=(1, 2)) - np.trace(matrix, axis1=1, axis2=2)) / (count * (count - 1))
    return diagonal - off_diagonal


def linear_cka_by_layer(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    values = []
    for x, y in zip(left.astype(np.float32), right.astype(np.float32)):
        x = x - x.mean(axis=0, keepdims=True)
        y = y - y.mean(axis=0, keepdims=True)
        gram_x, gram_y = x @ x.T, y @ y.T
        numerator = float(np.sum(gram_x * gram_y))
        denominator = float(np.linalg.norm(gram_x) * np.linalg.norm(gram_y))
        values.append(numerator / denominator if denominator else 0.0)
    return np.asarray(values, dtype=np.float32)


def binding_margin(state: np.ndarray, sources: np.ndarray, relevant_mask: list[bool]) -> np.ndarray:
    similarities = cosine(sources, state[:, None, :])
    mask = np.asarray(relevant_mask, dtype=bool)
    return similarities[:, mask].mean(axis=1) - similarities[:, ~mask].mean(axis=1)


def interval(values: np.ndarray, seed: int) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, values.shape[0], size=(BOOTSTRAPS, values.shape[0]))
    bootstrap = values[indices].mean(axis=1)
    return {
        "n_examples": int(values.shape[0]), "mean": values.mean(axis=0).tolist(),
        "bootstrap_95_ci_low": np.percentile(bootstrap, 2.5, axis=0).tolist(),
        "bootstrap_95_ci_high": np.percentile(bootstrap, 97.5, axis=0).tolist(),
        "bootstrap_replicates": BOOTSTRAPS,
    }


def scalar_interval(values: list[float], seed: int) -> dict[str, Any]:
    result = interval(np.asarray(values)[:, None], seed)
    return {"n_examples": result["n_examples"], "mean": result["mean"][0],
            "bootstrap_95_ci": [result["bootstrap_95_ci_low"][0], result["bootstrap_95_ci_high"][0]],
            "bootstrap_replicates": BOOTSTRAPS}


def load_activation(root: Path, record: dict[str, Any]) -> dict[str, np.ndarray]:
    with np.load(root / record["activation_file"]) as archive:
        return {name: archive[name] for name in archive.files}


def stage5_trace_observations(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = {}
    for condition in ("numeric", "random_compact", "uuid"):
        selected = [row for row in rows if row["identifier_condition"] == condition and row["require_citations"]]
        exact_relevant, avoids_all, shortened = [], [], []
        for row in selected:
            text = row["scratchpad"]
            mapping = row["identifier_mapping"]["citation_by_source"]
            relevant_labels = [mapping[key] for key in row["relevant_sources"]]
            all_labels = list(mapping.values())
            exact_relevant.append(any(label in text for label in relevant_labels))
            avoids_all.append(not any(label in text for label in all_labels))
            if condition == "uuid":
                shortened.append(any(label[1:-1].split("-", 1)[0] in text and label not in text for label in relevant_labels))
        result[condition] = {
            "n": len(selected), "mentions_exact_relevant_identifier": sum(exact_relevant) / len(selected),
            "avoids_identifiers": sum(avoids_all) / len(selected),
            "mentions_uuid_prefix_without_full_uuid": (sum(shortened) / len(shortened)) if shortened else None,
        }
    return result


def analyze(root: Path, stage5_path: Path | None) -> dict[str, Any]:
    records = [json.loads(line) for line in (root / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        grouped[record["example_id"]][record["identifier_condition"]] = record
    complete = {example: rows for example, rows in grouped.items() if set(rows) == set(CONDITIONS)}
    if len(complete) * len(CONDITIONS) != len(records):
        raise ValueError(f"Manifest is incomplete: {len(records)} rows, {len(complete)} complete examples")

    cross: dict[str, dict[str, list[np.ndarray]]] = {
        f"{left}_vs_{right}": defaultdict(list) for left, right in PAIRS
    }
    within: dict[str, dict[str, list[np.ndarray]]] = {condition: defaultdict(list) for condition in CONDITIONS}
    nlls: dict[str, dict[str, list[float]]] = {condition: defaultdict(list) for condition in CONDITIONS}
    layers = None
    for example_id, condition_records in sorted(complete.items()):
        arrays = {condition: load_activation(root, condition_records[condition]) for condition in CONDITIONS}
        if layers is None:
            layers = int(arrays[CONDITIONS[0]]["question"].shape[0])
        for left, right in PAIRS:
            label = f"{left}_vs_{right}"
            for source_field in ("source_label", "source_content"):
                cross[label][f"{source_field}_cosine"].append(
                    cosine(arrays[left][source_field], arrays[right][source_field]).mean(axis=1)
                )
                cross[label][f"{source_field}_alignment_margin"].append(
                    alignment_margin(arrays[left][source_field], arrays[right][source_field])
                )
                cross[label][f"{source_field}_cka"].append(
                    linear_cka_by_layer(arrays[left][source_field], arrays[right][source_field])
                )
            for field in VECTOR_FIELDS:
                cross[label][f"{field}_cosine"].append(cosine(arrays[left][field], arrays[right][field]))
        for condition in CONDITIONS:
            record, values = condition_records[condition], arrays[condition]
            within[condition]["pre_answer_content_binding_margin"].append(
                binding_margin(values["pre_answer"], values["source_content"], record["relevant_mask"])
            )
            within[condition]["pre_citation_label_binding_margin"].append(
                binding_margin(values["pre_citation"], values["source_label"], record["relevant_mask"])
            )
            nlls[condition]["answer_nll"].append(float(record["answer_nll"]))
            nlls[condition]["citation_nll"].append(float(record["citation_nll"]))
            nlls[condition]["answer_total_nll"].append(float(sum(record["answer_token_nll"])))
            nlls[condition]["citation_total_nll"].append(float(sum(record["citation_token_nll"])))
            nlls[condition]["citation_sequence_tokens"].append(float(len(record["citation_token_nll"])))
            token_lengths = record["identifier_mapping"]["token_lengths"]
            nlls[condition]["mean_identifier_tokens"].append(sum(token_lengths.values()) / len(token_lengths))

    assert layers is not None
    cross_summary = {}
    seed = 606000
    for pair, metrics in cross.items():
        cross_summary[pair] = {}
        for metric, values in metrics.items():
            seed += 1
            cross_summary[pair][metric] = interval(np.stack(values), seed)
    within_summary = {}
    for condition, metrics in within.items():
        within_summary[condition] = {}
        for metric, values in metrics.items():
            seed += 1
            within_summary[condition][metric] = interval(np.stack(values), seed)
    nll_summary = {}
    for condition, metrics in nlls.items():
        nll_summary[condition] = {}
        for metric, values in metrics.items():
            seed += 1
            nll_summary[condition][metric] = scalar_interval(values, seed)
    paired_nll = {}
    for left, right in PAIRS:
        label = f"{left}_vs_{right}"
        paired_nll[label] = {}
        for metric in ("answer_nll", "citation_nll", "answer_total_nll", "citation_total_nll"):
            deltas = np.asarray(nlls[right][metric]) - np.asarray(nlls[left][metric])
            seed += 1
            paired_nll[label][f"{right}_minus_{left}_{metric}"] = scalar_interval(deltas.tolist(), seed)
    structured_uuid = cross_summary["structured_vs_uuid"]
    label_cka = np.asarray(structured_uuid["source_label_cka"]["mean"])
    peak_layer = int(np.argmax(label_cka))
    binding_layers = list(range(max(1, peak_layer - 2), min(layers - 1, peak_layer + 2) + 1))
    output_start = max(1, int(np.floor(0.70 * (layers - 1))))
    fact_cka_min = float(np.min(structured_uuid["source_content_cka"]["mean"]))
    label_cka_gain = float(label_cka[peak_layer] - label_cka[0])
    late_specificity_gap = float(
        structured_uuid["question_cosine"]["mean"][-1]
        - structured_uuid["pre_citation_cosine"]["mean"][-1]
    )
    signature_present = fact_cka_min >= 0.90 and label_cka_gain >= 0.10 and late_specificity_gap >= 0.05
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    return {
        "activation_dir": str(root), "records": len(records), "complete_paired_examples": len(complete),
        "conditions": list(CONDITIONS), "layers": layers, "hidden_size": metadata["hidden_size"],
        "model": metadata["config"]["backend"]["model"], "model_revision": metadata["config"]["backend"]["revision"],
        "cross_condition": cross_summary, "within_condition": within_summary,
        "token_likelihoods": nll_summary, "paired_token_likelihood_effects": paired_nll,
        "behavioral_trace_observations": stage5_trace_observations(stage5_path),
        "checkpoint6": {
            "decision": "proceed_to_targeted_stage7" if signature_present else "no_clear_stage7_gate",
            "candidate_binding_layers": binding_layers,
            "candidate_output_layers": list(range(output_start, layers)),
            "label_cka_peak_layer": peak_layer,
            "label_cka_gain_from_embedding": label_cka_gain,
            "minimum_source_fact_cka": fact_cka_min,
            "late_question_minus_precitation_cosine": late_specificity_gap,
            "evidence_type": "correlational representation-level signature",
            "required_next_evidence": "causal source-ID swap or activation patching",
        },
    }


def curve_point(metric: dict[str, Any], layer: int) -> str:
    return (f"{metric['mean'][layer]:.3f} "
            f"[{metric['bootstrap_95_ci_low'][layer]:.3f}, {metric['bootstrap_95_ci_high'][layer]:.3f}]")


def scalar_point(metric: dict[str, Any]) -> str:
    low, high = metric["bootstrap_95_ci"]
    return f"{metric['mean']:.3f} [{low:.3f}, {high:.3f}]"


def report(result: dict[str, Any]) -> str:
    last = result["layers"] - 1
    selected_layers = sorted(set((0, round(last * 0.25), round(last * 0.50), round(last * 0.75), last)))
    pair = result["cross_condition"]["structured_vs_uuid"]
    lines = [
        "# Stage 6: explicit vs implicit symbolic compression", "",
        f"**Design:** {result['complete_paired_examples']} semantic examples × 3 identifier formats = "
        f"{result['records']} paired forward passes through `{result['model']}`. The model has "
        f"{result['layers'] - 1} transformer blocks plus the embedding state ({result['layers']} stored layers) "
        f"and hidden width {result['hidden_size']}.", "",
        "The same source order, source facts, question, answer, and relevant-source set are used across `[S1]`, "
        "compact arbitrary, and UUID conditions. Answer and citation states are teacher-forced so token spans align; "
        "they are representation measurements, not generated-answer accuracy estimates.", "",
        "All intervals are 5,000-replicate paired bootstraps over complete semantic examples.", "",
        "## Structured versus UUID representation similarity", "",
        "| Layer | Source-label cosine | Source-fact cosine | Question cosine | Pre-answer cosine | Answer cosine | Pre-citation cosine | Citation cosine |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for layer in selected_layers:
        lines.append(
            f"| {layer} | {curve_point(pair['source_label_cosine'], layer)} | "
            f"{curve_point(pair['source_content_cosine'], layer)} | {curve_point(pair['question_cosine'], layer)} | "
            f"{curve_point(pair['pre_answer_cosine'], layer)} | {curve_point(pair['answer_cosine'], layer)} | "
            f"{curve_point(pair['pre_citation_cosine'], layer)} | {curve_point(pair['citation_cosine'], layer)} |"
        )
    lines.extend(("", "## Source-identity geometry", "",
                  "Alignment margin is matched-source cosine minus the mean mismatched-source cosine. CKA compares "
                  "the full set of source vectors across formats.", "",
                  "| Layer | Label alignment margin | Fact alignment margin | Label CKA | Fact CKA |",
                  "|---:|---:|---:|---:|---:|"))
    for layer in selected_layers:
        lines.append(
            f"| {layer} | {curve_point(pair['source_label_alignment_margin'], layer)} | "
            f"{curve_point(pair['source_content_alignment_margin'], layer)} | "
            f"{curve_point(pair['source_label_cka'], layer)} | {curve_point(pair['source_content_cka'], layer)} |"
        )
    lines.extend(("", "## Within-condition binding geometry", "",
                  "Positive margins mean the state is more cosine-aligned with relevant than distractor sources.", "",
                  "| Condition | Layer | Pre-answer → source-fact margin | Pre-citation → source-label margin |",
                  "|---|---:|---:|---:|"))
    for condition in CONDITIONS:
        metrics = result["within_condition"][condition]
        for layer in selected_layers:
            lines.append(
                f"| {condition} | {layer} | {curve_point(metrics['pre_answer_content_binding_margin'], layer)} | "
                f"{curve_point(metrics['pre_citation_label_binding_margin'], layer)} |"
            )
    lines.extend(("", "## Exact-token reconstruction cost", "",
                  "NLL is mean negative log likelihood per teacher-forced answer or citation token; lower is easier.", "",
                  "| Condition | Mean identifier tokens | Citation sequence tokens | Answer NLL/token | Citation NLL/token | Citation total NLL |",
                  "|---|---:|---:|---:|---:|---:|"))
    for condition in CONDITIONS:
        metrics = result["token_likelihoods"][condition]
        lines.append(
            f"| {condition} | {scalar_point(metrics['mean_identifier_tokens'])} | "
            f"{scalar_point(metrics['citation_sequence_tokens'])} | {scalar_point(metrics['answer_nll'])} | "
            f"{scalar_point(metrics['citation_nll'])} | {scalar_point(metrics['citation_total_nll'])} |"
        )
    lines.extend(("", "### Paired UUID cost", ""))
    effects = result["paired_token_likelihood_effects"]["structured_vs_uuid"]
    for name, metric in effects.items():
        lines.append(f"- `{name}`: {scalar_point(metric)}")
    traces = result.get("behavioral_trace_observations", {})
    if traces:
        lines.extend(("", "## Observable Stage 5 scratchpad behavior", "",
                      "These trace statistics are behavioral signals only, not mechanistic evidence.", "",
                      "| Identifier | Rows | Mentions exact relevant ID | Avoids all IDs | Shortened UUID prefix |",
                      "|---|---:|---:|---:|---:|"))
        for condition, values in traces.items():
            prefix = values["mentions_uuid_prefix_without_full_uuid"]
            lines.append(
                f"| {condition} | {values['n']} | {100 * values['mentions_exact_relevant_identifier']:.1f}% | "
                f"{100 * values['avoids_identifiers']:.1f}% | "
                f"{'—' if prefix is None else f'{100 * prefix:.1f}%'} |"
            )
    gate = result["checkpoint6"]
    label_cka = pair["source_label_cka"]["mean"]
    fact_cka = pair["source_content_cka"]["mean"]
    peak = gate["label_cka_peak_layer"]
    decision = gate["decision"].replace("_", " ")
    uuid_effects = result["paired_token_likelihood_effects"]["structured_vs_uuid"]
    answer_delta = uuid_effects["uuid_minus_structured_answer_nll"]["mean"]
    citation_delta = uuid_effects["uuid_minus_structured_citation_total_nll"]["mean"]
    lines.extend(("", "## Checkpoint 6 interpretation", "",
                  f"**Gate decision: {decision}.**", "",
                  f"Structured-versus-UUID source-label relational geometry starts at CKA {label_cka[0]:.3f} "
                  f"and peaks at layer {peak} (CKA {label_cka[peak]:.3f}). Source-fact CKA remains at least "
                  f"{min(fact_cka):.3f}. At the final layer, question cosine is "
                  f"{pair['question_cosine']['mean'][-1]:.3f}, pre-citation cosine is "
                  f"{pair['pre_citation_cosine']['mean'][-1]:.3f}, and citation cosine is "
                  f"{pair['citation_cosine']['mean'][-1]:.3f}.", "",
                  f"The paired UUID-minus-structured teacher-forced answer NLL difference is {answer_delta:+.3f}; "
                  f"the total citation NLL difference is {citation_delta:+.3f}. These likelihood measurements test "
                  "literal reconstruction cost, while the representation curves test format-dependent state geometry.", "",
                  f"The signature is correlational. If taken to Stage 7, patch or swap activations first at layers "
                  f"{gate['candidate_binding_layers']} and compare the late output region "
                  f"{gate['candidate_output_layers']}. Attention plots or probes alone are insufficient for the causal gate.", ""))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("activation_dir")
    parser.add_argument("--stage5-jsonl")
    parser.add_argument("--json-output", default="results/processed/stage6_qwen25_15b.json")
    parser.add_argument("--report-output", default="FINDINGS_STAGE6.md")
    args = parser.parse_args()
    result = analyze(Path(args.activation_dir), Path(args.stage5_jsonl) if args.stage5_jsonl else None)
    json_path, report_path = Path(args.json_output), Path(args.report_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(report(result), encoding="utf-8")
    print(json.dumps({"records": result["records"], "examples": result["complete_paired_examples"],
                      "json": str(json_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

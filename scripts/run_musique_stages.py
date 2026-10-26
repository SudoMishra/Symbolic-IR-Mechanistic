#!/usr/bin/env python3
"""Run the paired MuSiQue Stage 2-4 scenario matrix for one model."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.config import ExperimentConfig, load_config  # noqa: E402
from symbolic_ir.data.musique import load_musique_examples  # noqa: E402
from symbolic_ir.evaluation import evaluate_output  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.inference import create_backend  # noqa: E402
from symbolic_ir.prompts import render_prompt  # noqa: E402
from symbolic_ir.runner import JsonlStore, reproducibility_metadata  # noqa: E402
from symbolic_ir.schema import GenerationRequest  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def request_key(config: ExperimentConfig, scenario: str, example_id: str, condition: str, required: bool) -> str:
    payload = json.dumps([config.digest, scenario, example_id, condition, required], separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


def iter_matrix(config: ExperimentConfig, tokenizer: Any) -> Iterator[tuple[dict[str, Any], Any]]:
    dataset = dict(config.dataset)
    scenarios = list(dataset.pop("scenarios"))
    dataset["data_path"] = str(resolve(str(dataset["data_path"])))
    dataset["selection_path"] = str(resolve(str(dataset["selection_path"])))
    for scenario in scenarios:
        cell = {**dataset, "num_sources": int(scenario["num_sources"])}
        examples = load_musique_examples(cell, config.seed)
        controls = scenario.get("controls") or [
            {"identifier": condition, "require_citations": True}
            for condition in scenario["identifiers"]
        ]
        for example in examples:
            for control in controls:
                condition = str(control["identifier"])
                required = bool(control.get("require_citations", True))
                mapping = render_identifiers(example.sources, condition, config.seed, tokenizer)
                rendered = render_prompt(example, mapping, require_citations=required)
                yield {
                    "stage": int(scenario["stage"]),
                    "scenario": str(scenario["name"]),
                    "num_sources": int(scenario["num_sources"]),
                    "condition": condition,
                    "require_citations": required,
                    "request_key": request_key(config, str(scenario["name"]), example.example_id, condition, required),
                    "validated_prompt_tokens": tokenizer.count(rendered.prompt),
                }, rendered


def validate(config: ExperimentConfig) -> tuple[list[tuple[dict[str, Any], Any]], Any, dict[str, Any]]:
    tokenizer = create_token_counter(config.generation.get("tokenizer"))
    matrix = list(iter_matrix(config, tokenizer))
    bounds = config.dataset["prompt_tokens"]
    outside = [
        context for context, _ in matrix
        if not int(bounds["min"]) <= context["validated_prompt_tokens"] <= int(bounds["max"])
    ]
    if outside:
        first = outside[0]
        raise ValueError(
            f"{len(outside)} prompts outside configured range; first is "
            f"{first['scenario']} {first['condition']} at {first['validated_prompt_tokens']} tokens"
        )
    by_stage: dict[int, int] = {}
    for context, _ in matrix:
        by_stage[context["stage"]] = by_stage.get(context["stage"], 0) + 1
    lengths = [context["validated_prompt_tokens"] for context, _ in matrix]
    summary = {
        "requests": len(matrix), "by_stage": by_stage,
        "prompt_tokens": {"min": min(lengths), "mean": round(sum(lengths) / len(lengths), 1), "max": max(lengths)},
        "tokenizer": tokenizer.name,
    }
    return matrix, tokenizer, summary


def run(config: ExperimentConfig, limit: int | None = None, validate_only: bool = False) -> tuple[Path | None, dict[str, Any]]:
    matrix, tokenizer, summary = validate(config)
    if validate_only:
        return None, summary
    backend = create_backend(config.backend)
    output = resolve(config.output_dir) / config.name / f"{config.digest}.jsonl"
    store = JsonlStore(output)
    metadata_path = output.with_suffix(".metadata.json")
    if not metadata_path.exists():
        metadata = reproducibility_metadata(config, tokenizer.name)
        metadata["dataset_provenance"] = {
            "repository": "https://github.com/StonyBrookNLP/musique",
            "split": "musique_ans_v1.0_dev.jsonl",
            "data_sha256": sha256(resolve(str(config.dataset["data_path"]))),
            "selection_sha256": sha256(resolve(str(config.dataset["selection_path"]))),
        }
        metadata["validated_matrix"] = summary
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    completed = store.completed_keys()
    counts: dict[str, Any] = {"planned": 0, "completed": 0, "skipped": 0, **summary}
    for context, rendered in matrix[:limit]:
        counts["planned"] += 1
        if context["request_key"] in completed:
            counts["skipped"] += 1
            continue
        request = GenerationRequest(
            prompt=rendered.prompt,
            example_id=rendered.canonical.example_id,
            max_output_tokens=int(config.generation.get("max_output_tokens", 256)),
            temperature=float(config.generation.get("temperature", 0.0)),
            metadata={"generation_seed": config.seed, "request_key": context["request_key"]},
        )
        response = backend.generate(request)
        evaluation = evaluate_output(rendered, response.text)
        store.append({
            "request_key": context["request_key"], "example_id": request.example_id,
            "source_dataset_id": rendered.canonical.metadata["source_id"],
            "dataset": rendered.canonical.metadata["dataset"],
            "stage": context["stage"], "scenario": context["scenario"],
            "task_type": rendered.canonical.task_type, "hop_count": rendered.canonical.metadata["hop_count"],
            "model": response.model, "model_revision": response.model_revision,
            "prompt_version": "musique-citation-v1", "prompt": rendered.prompt,
            "identifier_condition": rendered.mapping.condition,
            "identifier_mapping": asdict(rendered.mapping),
            "identifier_token_lengths": rendered.mapping.token_lengths,
            "source_order": list(rendered.source_order),
            "relevant_sources": list(rendered.canonical.relevant_sources),
            "require_citations": rendered.require_citations,
            "generation_parameters": {
                "max_output_tokens": request.max_output_tokens,
                "temperature": request.temperature,
                "n_ctx": config.backend.get("n_ctx"),
            },
            "raw_output": response.text, "raw_response": response.raw,
            "parsed_answer": evaluation["parsed_answer"],
            "parsed_citations": evaluation["parsed_citations"],
            "evaluation": evaluation,
            "token_counts": {
                "validated_prompt": context["validated_prompt_tokens"],
                "input": response.input_tokens, "output": response.output_tokens,
                "reasoning": response.reasoning_tokens,
            },
            "hit_generation_cap": response.output_tokens == request.max_output_tokens,
            "latency": response.latency_seconds,
            "dataset_cell": {"num_sources": context["num_sources"], "hop_count": rendered.canonical.metadata["hop_count"]},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        completed.add(context["request_key"])
        counts["completed"] += 1
    return output, counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    output, counts = run(load_config(resolve(args.config)), args.limit, args.validate_only)
    print(json.dumps({"output": str(output) if output else None, **counts}, indent=2))


if __name__ == "__main__":
    main()

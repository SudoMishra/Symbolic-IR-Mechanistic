#!/usr/bin/env python3
"""Validate or run the public LongProc ToM 2K-output experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.config import ExperimentConfig, load_config  # noqa: E402
from symbolic_ir.evaluation.longproc import evaluate_tom_trace  # noqa: E402
from symbolic_ir.inference import create_backend  # noqa: E402
from symbolic_ir.runner import JsonlStore, reproducibility_metadata  # noqa: E402
from symbolic_ir.schema import GenerationRequest  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402


def _resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _request_key(config: ExperimentConfig, source_index: int) -> str:
    payload = json.dumps([config.digest, source_index], separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


def load_selected(config: ExperimentConfig) -> tuple[list[dict[str, Any]], str, list[int]]:
    dataset = config.dataset
    if dataset.get("family") != "longproc_tom_tracking":
        raise ValueError("This runner requires dataset.family: longproc_tom_tracking")
    data = json.loads(_resolve(str(dataset["data_path"])).read_text(encoding="utf-8"))
    prompts = yaml.safe_load(_resolve(str(dataset["prompt_path"])).read_text(encoding="utf-8"))
    selection = json.loads(_resolve(str(dataset["selection_path"])).read_text(encoding="utf-8"))
    indices = [int(index) for index in selection["indices"]]
    if len(indices) != int(dataset["count"]):
        raise ValueError(f"Selection has {len(indices)} examples; config declares {dataset['count']}")
    return [data[index] for index in indices], str(prompts["USER_PROMPT"]), indices


def validate_lengths(
    config: ExperimentConfig,
    examples: list[dict[str, Any]],
    template: str,
    indices: list[int],
) -> tuple[list[dict[str, Any]], Any]:
    tokenizer = create_token_counter(config.generation.get("tokenizer"))
    prompt_bounds = config.dataset["prompt_tokens"]
    reference_bounds = config.dataset["reference_tokens"]
    validated = []
    for example, source_index in zip(examples, indices):
        prompt = template.format(story=example["story"], question=example["question"])
        reference = str(example["solution"])
        prompt_tokens = tokenizer.count(prompt)
        reference_tokens = tokenizer.count(reference)
        if not int(prompt_bounds["min"]) <= prompt_tokens <= int(prompt_bounds["max"]):
            raise ValueError(f"Example {source_index}: prompt length {prompt_tokens} outside configured range")
        if not int(reference_bounds["min"]) <= reference_tokens <= int(reference_bounds["max"]):
            raise ValueError(f"Example {source_index}: reference length {reference_tokens} outside configured range")
        validated.append({
            "source_index": source_index,
            "prompt": prompt,
            "reference": reference,
            "prompt_tokens": prompt_tokens,
            "reference_tokens": reference_tokens,
            "question": example["question"],
            "answer": example["answer"],
        })
    return validated, tokenizer


def describe(examples: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    def summary(field: str) -> dict[str, float]:
        values = [int(example[field]) for example in examples]
        return {"min": min(values), "mean": round(sum(values) / len(values), 1), "max": max(values)}
    return {"prompt_tokens": summary("prompt_tokens"), "reference_tokens": summary("reference_tokens")}


def run(config: ExperimentConfig, *, limit: int | None = None, validate_only: bool = False) -> tuple[Path | None, dict[str, Any]]:
    source_examples, template, indices = load_selected(config)
    examples, tokenizer = validate_lengths(config, source_examples, template, indices)
    length_summary = describe(examples)
    if validate_only:
        return None, {"examples": len(examples), "tokenizer": tokenizer.name, **length_summary}

    backend = create_backend(config.backend)
    output_path = _resolve(config.output_dir) / config.name / f"{config.digest}.jsonl"
    store = JsonlStore(output_path)
    metadata_path = output_path.with_suffix(".metadata.json")
    if not metadata_path.exists():
        metadata = reproducibility_metadata(config, tokenizer.name)
        metadata["dataset_provenance"] = {
            "repository": "https://github.com/princeton-pli/LongProc",
            "revision": config.dataset["source_revision"],
            "data_sha256": _sha256(_resolve(str(config.dataset["data_path"]))),
            "prompt_sha256": _sha256(_resolve(str(config.dataset["prompt_path"]))),
            "selected_source_indices": indices,
        }
        metadata["validated_lengths"] = length_summary
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    completed = store.completed_keys()
    counts: dict[str, Any] = {"planned": 0, "completed": 0, "skipped": 0, **length_summary}
    for example in examples[:limit]:
        counts["planned"] += 1
        key = _request_key(config, example["source_index"])
        if key in completed:
            counts["skipped"] += 1
            continue
        request = GenerationRequest(
            prompt=example["prompt"],
            example_id=f"longproc-tom-2k-{example['source_index']:03d}",
            max_output_tokens=int(config.generation["max_output_tokens"]),
            temperature=float(config.generation.get("temperature", 0.0)),
            metadata={"generation_seed": config.seed, "request_key": key},
        )
        response = backend.generate(request)
        evaluation = evaluate_tom_trace(response.text, example["reference"])
        store.append({
            "request_key": key,
            "example_id": request.example_id,
            "source_index": example["source_index"],
            "dataset": "LongProc/tom_tracking_2k",
            "dataset_revision": config.dataset["source_revision"],
            "model": response.model,
            "model_revision": response.model_revision,
            "prompt_version": "longproc-official-tom-prompts.yaml",
            "prompt": example["prompt"],
            "question": example["question"],
            "reference_output": example["reference"],
            "reference_final_answer": example["answer"],
            "generation_parameters": {
                "max_output_tokens": request.max_output_tokens,
                "temperature": request.temperature,
                "n_ctx": config.backend.get("n_ctx"),
            },
            "raw_output": response.text,
            "raw_response": response.raw,
            "evaluation": evaluation,
            "token_counts": {
                "validated_prompt": example["prompt_tokens"],
                "validated_reference": example["reference_tokens"],
                "input": response.input_tokens,
                "output": response.output_tokens,
                "reasoning": response.reasoning_tokens,
            },
            "hit_generation_cap": response.output_tokens == request.max_output_tokens,
            "latency": response.latency_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        completed.add(key)
        counts["completed"] += 1
    return output_path, counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    config = load_config(_resolve(args.config))
    output, counts = run(config, limit=args.limit, validate_only=args.validate_only)
    print(json.dumps({"output": str(output) if output else None, **counts}, indent=2))


if __name__ == "__main__":
    main()

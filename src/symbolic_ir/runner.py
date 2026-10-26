"""Append-only, resumable paired experiment runner."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from symbolic_ir.config import ExperimentConfig, expand_grid
from symbolic_ir.data import generate_examples
from symbolic_ir.evaluation import evaluate_output
from symbolic_ir.identifiers import render_identifiers
from symbolic_ir.inference import create_backend
from symbolic_ir.prompts import render_prompt
from symbolic_ir.schema import GenerationRequest, IdentifierMapping
from symbolic_ir.tokenization import create_token_counter


def _stable_key(*values: object) -> str:
    payload = json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


def _git_revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def reproducibility_metadata(config: ExperimentConfig, tokenizer_name: str) -> dict[str, Any]:
    return {
        "experiment": config.name, "config_digest": config.digest,
        "created_at": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "platform": platform.platform(), "git_revision": _git_revision(),
        "tokenizer": tokenizer_name, "pid": os.getpid(), "config": config.to_dict(),
    }


class JsonlStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def completed_keys(self) -> set[str]:
        if not self.path.exists():
            return set()
        keys = set()
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                try:
                    keys.add(str(json.loads(line)["request_key"]))
                except (json.JSONDecodeError, KeyError) as exc:
                    raise ValueError(f"Invalid record at {self.path}:{line_number}") from exc
        return keys

    def append(self, record: dict[str, Any]) -> None:
        # O_APPEND keeps each compact JSON record an indivisible write for normal local filesystems.
        payload = (json.dumps(record, sort_keys=True, ensure_ascii=False, default=str) + "\n").encode()
        descriptor = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def iter_requests(config: ExperimentConfig) -> Iterator[tuple[dict[str, Any], Any]]:
    tokenizer = create_token_counter(config.generation.get("tokenizer"))
    condition_controls = config.generation.get("condition_controls")
    if condition_controls is not None:
        pairs = [
            (str(control["identifier"]), bool(control.get("require_citations", True)))
            for control in condition_controls
        ]
    else:
        require_values = config.generation.get("require_citations", [True])
        if not isinstance(require_values, list):
            require_values = [require_values]
        pairs = [(condition, bool(required)) for condition in config.identifiers for required in require_values]
    budgets = config.generation.get("reasoning_budgets", [config.generation.get("reasoning_budget")])
    if not isinstance(budgets, list):
        budgets = [budgets]
    for cell_index, cell in enumerate(expand_grid(config)):
        examples = generate_examples(cell, config.seed)
        for example in examples:
            for condition, require_citations in pairs:
                mapping = render_identifiers(example.sources, condition, config.seed, tokenizer)
                fixed_source_condition = config.generation.get("fixed_source_identifiers")
                if fixed_source_condition:
                    fixed = render_identifiers(
                        example.sources, str(fixed_source_condition), config.seed, tokenizer
                    )
                    # Preserve the entity-representation condition so the PII
                    # renderer applies the intended masking, while holding the
                    # source-label surface form constant across paired prompts.
                    mapping = IdentifierMapping(
                        condition=condition,
                        display_by_source=fixed.display_by_source,
                        citation_by_source=fixed.citation_by_source,
                        token_lengths=fixed.token_lengths,
                    )
                rendered = render_prompt(example, mapping, require_citations=require_citations)
                for budget in budgets:
                    key = _stable_key(config.digest, cell_index, example.example_id, condition, require_citations, budget)
                    yield {
                        "request_key": key, "cell": cell, "cell_index": cell_index,
                        "reasoning_budget": budget, "require_citations": require_citations,
                        "tokenizer_name": tokenizer.name,
                    }, rendered


def run_experiment(config: ExperimentConfig, *, limit: int | None = None) -> tuple[Path, dict[str, int]]:
    tokenizer = create_token_counter(config.generation.get("tokenizer"))
    backend = create_backend(config.backend)
    output_path = Path(config.output_dir) / config.name / f"{config.digest}.jsonl"
    store = JsonlStore(output_path)
    metadata_path = output_path.with_suffix(".metadata.json")
    if not metadata_path.exists():
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(reproducibility_metadata(config, tokenizer.name), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    completed = store.completed_keys()
    counts = {"planned": 0, "completed": 0, "skipped": 0}
    for context, rendered in iter_requests(config):
        if limit is not None and counts["planned"] >= limit:
            break
        counts["planned"] += 1
        if context["request_key"] in completed:
            counts["skipped"] += 1
            continue
        expected_citations = [rendered.mapping.citation_by_source[key] for key in rendered.canonical.relevant_sources]
        request = GenerationRequest(
            prompt=rendered.prompt, example_id=rendered.canonical.example_id,
            max_output_tokens=int(config.generation.get("max_output_tokens", 256)),
            temperature=float(config.generation.get("temperature", 0.0)),
            reasoning_budget=context["reasoning_budget"],
            metadata={
                "request_key": context["request_key"],
                "expected_answer": rendered.expected_answer or rendered.canonical.answer,
                "expected_citations": expected_citations,
                "require_citations": rendered.require_citations,
                "generation_seed": config.seed,
            },
        )
        response = backend.generate(request)
        evaluation = evaluate_output(rendered, response.text)
        record = {
            "request_key": context["request_key"], "example_id": rendered.canonical.example_id,
            "seed": rendered.canonical.seed, "task_type": rendered.canonical.task_type,
            "model": response.model, "model_revision": response.model_revision,
            "prompt_version": "citation-prompt-v1", "prompt": rendered.prompt,
            "identifier_condition": rendered.mapping.condition,
            "identifier_mapping": asdict(rendered.mapping),
            "identifier_token_lengths": rendered.mapping.token_lengths,
            "source_order": list(rendered.source_order),
            "relevant_sources": list(rendered.canonical.relevant_sources),
            "reasoning_budget": request.reasoning_budget,
            "require_citations": rendered.require_citations,
            "generation_parameters": {"max_output_tokens": request.max_output_tokens, "temperature": request.temperature},
            "raw_output": response.text, "raw_response": response.raw,
            "parsed_answer": evaluation["parsed_answer"], "parsed_citations": evaluation["parsed_citations"],
            "evaluation": evaluation,
            "token_counts": {"input": response.input_tokens, "output": response.output_tokens, "reasoning": response.reasoning_tokens},
            "latency": response.latency_seconds, "dataset_cell": context["cell"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        store.append(record)
        completed.add(context["request_key"])
        counts["completed"] += 1
        progress_every = int(config.generation.get("progress_every", 0))
        if progress_every and counts["planned"] % progress_every == 0:
            print(json.dumps({"progress": counts["planned"], **counts}), flush=True)
    return output_path, counts

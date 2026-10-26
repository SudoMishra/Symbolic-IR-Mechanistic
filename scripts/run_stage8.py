#!/usr/bin/env python3
"""Validate and run the Stage 8 synthetic entity-canonicalization matrix."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.config import load_config  # noqa: E402
from symbolic_ir.runner import iter_requests, run_experiment  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def validate(config, limit: int | None = None):
    tokenizer = create_token_counter(config.generation.get("tokenizer"))
    lengths = defaultdict(list)
    source_label_sets = defaultdict(set)
    examples = set()
    requests = 0
    for context, rendered in iter_requests(config):
        if limit is not None and requests >= limit:
            break
        requests += 1
        examples.add(rendered.canonical.example_id)
        condition = rendered.mapping.condition
        lengths[condition].append(tokenizer.count(rendered.prompt))
        source_label_sets[condition].add(tuple(rendered.mapping.display_by_source.values()))
    bounds = config.dataset.get("prompt_tokens")
    all_lengths = [value for values in lengths.values() for value in values]
    if bounds and any(not int(bounds["min"]) <= value <= int(bounds["max"]) for value in all_lengths):
        outside = [value for value in all_lengths if not int(bounds["min"]) <= value <= int(bounds["max"])]
        raise ValueError(f"{len(outside)} prompts outside configured bounds; first={outside[0]}")
    if config.generation.get("fixed_source_identifiers"):
        canonical_sets = {values for condition in source_label_sets.values() for values in condition}
        expected_cells = len({len(value) for value in canonical_sets})
        if len(canonical_sets) != expected_cells:
            raise ValueError("Source identifiers differ across entity-representation conditions")
    return {
        "requests": requests, "semantic_examples": len(examples),
        "prompt_tokens": {
            condition: {"min": min(values), "mean": round(sum(values) / len(values), 1), "max": max(values)}
            for condition, values in lengths.items()
        },
        "source_identifier_condition": config.generation.get("fixed_source_identifiers"),
        "require_citations": config.generation.get("require_citations", True),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    config = load_config(resolve(args.config))
    summary = validate(config, args.limit)
    if args.validate_only:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    path, counts = run_experiment(config, limit=args.limit)
    print(json.dumps({**summary, "output": str(path), "counts": counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Phase 1: Stratified dataset generation for Stage 7B circuit localization.

Generates three non-overlapping, balanced splits:
1. Discovery split: N=32 semantic examples (96 counterfactual cases across 3 identifier conditions)
2. Validation split: N=32 semantic examples (96 counterfactual cases)
3. Confirmation split: N=80 semantic examples (240 counterfactual cases)

Stratification matrix per split:
- Task type: 50% temporal reasoning, 50% entity resolution
- Source count: 50% 15 sources, 50% 20 sources
- Identifier conditions: structured, random_compact, uuid
- Target position: balanced early, mid, late
- Permutation integrity: distinct seeds per split (202671, 202672, 202673)
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.data.reasoning import generate_reasoning_examples  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.mechinterp.swaps import swap_source_identifiers  # noqa: E402
from symbolic_ir.prompts import render_prompt  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402


IDENTIFIER_CONDITIONS = ("structured", "random_compact", "uuid")


def position_bucket(index: int, total: int) -> str:
    fraction = index / total
    if fraction < 0.33:
        return "early"
    elif fraction < 0.66:
        return "mid"
    return "late"


def build_split(
    split_name: str,
    target_count: int,
    base_seed: int,
    output_path: Path,
) -> dict[str, Any]:
    print(f"\nBuilding {split_name} split (target: {target_count} semantic examples)...")
    
    # We want equal representation across (task_type, num_sources)
    tasks = ["temporal", "entity_resolution"]
    sources_list = [15, 20]
    cells = [(t, s) for t in tasks for s in sources_list]
    per_cell = target_count // len(cells)
    remainder = target_count % len(cells)

    counter = create_token_counter({"type": "regex"})
    examples_collected = []
    cases_collected = []

    position_counts = {"early": 0, "mid": 0, "late": 0}
    task_counts = {t: 0 for t in tasks}
    source_counts = {s: 0 for s in sources_list}

    cell_seed = base_seed
    for cell_idx, (task_type, num_sources) in enumerate(cells):
        count_for_cell = per_cell + (1 if cell_idx < remainder else 0)
        # Generate with specific seed offset
        cell_seed += 100
        raw_examples = generate_reasoning_examples(
            seed=cell_seed,
            count=count_for_cell,
            num_sources=num_sources,
            task_type=task_type,
            long_context=True,
            filler_words=114,
        )

        for ex in raw_examples:
            # Determine relevant source position index
            relevant_key = ex.relevant_sources[0]
            rel_idx = next(i for i, s in enumerate(ex.sources) if s.key == relevant_key)
            bucket = position_bucket(rel_idx, len(ex.sources))
            position_counts[bucket] += 1
            task_counts[task_type] += 1
            source_counts[num_sources] += 1
            examples_collected.append(ex)

            # Pick distractor source (not relevant)
            distractor_key = next(s.key for s in ex.sources if s.key != relevant_key)

            # Generate counterfactual pairs for each identifier condition
            for condition in IDENTIFIER_CONDITIONS:
                clean_mapping = render_identifiers(ex.sources, condition, cell_seed, counter)
                swapped_mapping = swap_source_identifiers(clean_mapping, relevant_key, distractor_key)

                clean_rendered = render_prompt(ex, clean_mapping, require_citations=True)
                swapped_rendered = render_prompt(ex, swapped_mapping, require_citations=True)

                clean_label = clean_mapping.citation_by_source[relevant_key]
                swapped_label = swapped_mapping.citation_by_source[relevant_key]

                case = {
                    "split": split_name,
                    "example_id": ex.example_id,
                    "condition": condition,
                    "task_type": task_type,
                    "num_sources": num_sources,
                    "relevant_source_key": relevant_key,
                    "distractor_source_key": distractor_key,
                    "relevant_source_pos": rel_idx,
                    "position_bucket": bucket,
                    "clean_label": clean_label,
                    "swapped_label": swapped_label,
                    "clean_prompt": clean_rendered.prompt,
                    "swapped_prompt": swapped_rendered.prompt,
                    "clean_display_by_source": clean_mapping.display_by_source,
                    "swapped_display_by_source": swapped_mapping.display_by_source,
                    "source_order": list(clean_rendered.source_order),
                    "sources": [dataclasses.asdict(s) for s in ex.sources],
                    "question": ex.question,
                    "answer": ex.answer,
                }
                cases_collected.append(case)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    with output_path.open("w", encoding="utf-8") as f:
        for case in cases_collected:
            line = json.dumps(case) + "\n"
            f.write(line)
            hasher.update(line.encode("utf-8"))

    rel_file = str(output_path.relative_to(ROOT)) if output_path.is_relative_to(ROOT) else str(output_path)
    summary = {
        "split": split_name,
        "semantic_examples": len(examples_collected),
        "total_cases": len(cases_collected),
        "seed": base_seed,
        "task_distribution": task_counts,
        "source_distribution": source_counts,
        "position_distribution": position_counts,
        "file": rel_file,
        "sha256": hasher.hexdigest(),
    }
    print(f"  Generated {len(examples_collected)} examples -> {len(cases_collected)} cases.")
    print(f"  Tasks: {task_counts}, Sources: {source_counts}, Positions: {position_counts}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Generate circuit dataset splits")
    parser.add_argument("--outdir", default="data/circuit")
    args = parser.parse_args()

    out_dir = ROOT / args.outdir
    out_dir.mkdir(parents=True, exist_ok=True)

    splits_manifest = {}
    splits_manifest["discovery"] = build_split(
        "discovery", target_count=32, base_seed=202671,
        output_path=out_dir / "discovery_n32.jsonl"
    )
    splits_manifest["validation"] = build_split(
        "validation", target_count=32, base_seed=202672,
        output_path=out_dir / "validation_n32.jsonl"
    )
    splits_manifest["confirmation"] = build_split(
        "confirmation", target_count=80, base_seed=202673,
        output_path=out_dir / "confirmation_n80.jsonl"
    )

    manifest_path = out_dir / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(splits_manifest, indent=2), encoding="utf-8")
    print(f"\nSaved dataset manifest to: {manifest_path}")


if __name__ == "__main__":
    main()

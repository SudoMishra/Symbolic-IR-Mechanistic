"""Loader for the public MuSiQue-Answerable multi-hop QA dataset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from symbolic_ir.randomness import derive_seed
from symbolic_ir.schema import CanonicalExample, Source


def _paragraph_rank(seed: int, example_id: str, paragraph_index: int, purpose: str) -> int:
    return derive_seed(seed, "musique", purpose, example_id, paragraph_index)


def _select_paragraphs(record: dict[str, Any], num_sources: int, seed: int) -> list[dict[str, Any]]:
    paragraphs = list(record["paragraphs"])
    supporting = [paragraph for paragraph in paragraphs if paragraph["is_supporting"]]
    if num_sources < len(supporting):
        raise ValueError(f"num_sources={num_sources} cannot contain {len(supporting)} supporting paragraphs")
    if num_sources > len(paragraphs):
        raise ValueError(f"MuSiQue example {record['id']} has only {len(paragraphs)} paragraphs")
    distractors = sorted(
        (paragraph for paragraph in paragraphs if not paragraph["is_supporting"]),
        key=lambda paragraph: _paragraph_rank(seed, str(record["id"]), int(paragraph["idx"]), "include"),
    )
    selected = supporting + distractors[: num_sources - len(supporting)]
    return sorted(
        selected,
        key=lambda paragraph: _paragraph_rank(seed, str(record["id"]), int(paragraph["idx"]), "order"),
    )


def load_musique_examples(config: dict[str, Any], seed: int) -> list[CanonicalExample]:
    data_path = Path(str(config["data_path"]))
    records = [json.loads(line) for line in data_path.read_text(encoding="utf-8").splitlines() if line]
    by_id = {str(record["id"]): record for record in records}

    selection_path = config.get("selection_path")
    if selection_path:
        selection = json.loads(Path(str(selection_path)).read_text(encoding="utf-8"))
        selected_ids = [str(value) for value in selection["ids"]]
    else:
        selected_ids = sorted(by_id)
    missing = [example_id for example_id in selected_ids if example_id not in by_id]
    if missing:
        raise ValueError(f"MuSiQue selection contains unknown IDs: {missing[:3]}")

    num_sources = int(config.get("num_sources", 20))
    if config.get("skip_insufficient_sources", False):
        selected_ids = [
            example_id for example_id in selected_ids
            if len(by_id[example_id]["paragraphs"]) >= num_sources
        ]
    count = int(config.get("count", len(selected_ids)))
    selected_ids = selected_ids[:count]
    examples = []
    for example_id in selected_ids:
        record = by_id[example_id]
        paragraphs = _select_paragraphs(record, num_sources, seed)
        sources = tuple(
            Source(
                key=f"paragraph-{paragraph['idx']}",
                text=f"{paragraph['title']}\n{paragraph['paragraph_text']}",
                attributes={
                    "title": paragraph["title"],
                    "original_index": paragraph["idx"],
                    "is_supporting": bool(paragraph["is_supporting"]),
                    "entity_type": "SOURCE",
                },
            )
            for paragraph in paragraphs
        )
        relevant = tuple(source.key for source in sources if source.attributes["is_supporting"])
        decomposition = list(record.get("question_decomposition", []))
        examples.append(
            CanonicalExample(
                example_id=f"musique-{example_id}",
                seed=seed,
                task_type=f"{len(decomposition)}_hop",
                sources=sources,
                question=str(record["question"]),
                answer=str(record["answer"]),
                relevant_sources=relevant,
                claims=tuple(str(step.get("question", "")) for step in decomposition),
                metadata={
                    "dataset": "MuSiQue-Answerable v1.0 dev",
                    "source_id": example_id,
                    "hop_count": len(decomposition),
                    "answer_aliases": list(record.get("answer_aliases", [])),
                    "question_decomposition": decomposition,
                    "num_available_paragraphs": len(record["paragraphs"]),
                    "num_rendered_paragraphs": len(sources),
                },
            )
        )
    return examples

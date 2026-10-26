from __future__ import annotations

from typing import Any

from symbolic_ir.schema import CanonicalExample

from .citation import generate_citation_examples
from .musique import load_musique_examples
from .pii import generate_pii_examples
from .reasoning import generate_reasoning_examples


def generate_examples(config: dict[str, Any], seed: int) -> list[CanonicalExample]:
    family = str(config.get("family", "citation"))
    if family == "musique":
        return load_musique_examples(config, seed)
    kwargs = {
        "seed": seed,
        "count": int(config.get("count", 20)),
        "num_sources": int(config.get("num_sources", 5)),
        "task_type": str(config.get("task_type", "single_hop")),
    }
    if family == "citation":
        return generate_citation_examples(**kwargs)
    if family == "reasoning":
        return generate_reasoning_examples(
            **kwargs,
            long_context=bool(config.get("long_context", False)),
            filler_words=int(config.get("filler_words", 130)),
        )
    if family == "pii":
        return generate_pii_examples(
            **kwargs,
            long_context=bool(config.get("long_context", False)),
            filler_words=int(config.get("filler_words", 0)),
        )
    raise ValueError(f"Unknown dataset family: {family}")

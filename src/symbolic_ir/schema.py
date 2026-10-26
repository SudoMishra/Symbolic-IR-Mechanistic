"""Serializable domain models shared across datasets and experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Source:
    key: str
    text: str
    entity_key: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalExample:
    example_id: str
    seed: int
    task_type: str
    sources: tuple[Source, ...]
    question: str
    answer: str
    relevant_sources: tuple[str, ...]
    claims: tuple[str, ...] = ()
    entities: dict[str, dict[str, str]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IdentifierMapping:
    condition: str
    display_by_source: dict[str, str]
    citation_by_source: dict[str, str]
    token_lengths: dict[str, int]

    @property
    def source_by_citation(self) -> dict[str, str]:
        return {value: key for key, value in self.citation_by_source.items()}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderedExample:
    canonical: CanonicalExample
    mapping: IdentifierMapping
    prompt: str
    source_order: tuple[str, ...]
    require_citations: bool = True
    expected_answer: str | None = None
    protected_values: tuple[str, ...] = ()


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    example_id: str
    max_output_tokens: int = 256
    temperature: float = 0.0
    reasoning_budget: str | int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationResponse:
    text: str
    model: str
    model_revision: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    latency_seconds: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)

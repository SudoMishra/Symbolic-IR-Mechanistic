"""Deterministic identifier renderers for all behavioral conditions."""

from __future__ import annotations

import hashlib
import string
import uuid
from collections.abc import Callable, Sequence

from symbolic_ir.randomness import derive_seed, rng_for
from symbolic_ir.schema import IdentifierMapping, Source
from symbolic_ir.tokenization import TokenCounter


Renderer = Callable[[int, Source, int], str]


def _numeric(seed: int, source: Source, position: int) -> str:
    return f"[{position}]"


def _structured(seed: int, source: Source, position: int) -> str:
    return f"[S{position}]"


def _arbitrary(seed: int, source: Source, position: int) -> str:
    return f"[X{position}]"


def _semantic(seed: int, source: Source, position: int) -> str:
    return f"<source-{position}>"


def _random_chars(seed: int, source: Source, position: int, length: int) -> str:
    rng = rng_for(seed, "identifier", source.key, position, length)
    alphabet = string.ascii_uppercase + string.digits
    return "".join(rng.choice(alphabet) for _ in range(length))


def _compact(seed: int, source: Source, position: int) -> str:
    return f"[{_random_chars(seed, source, position, 4)}]"


def _hex(seed: int, source: Source, position: int, length: int) -> str:
    material = f"{seed}:{source.key}:{position}:{length}".encode()
    return f"[{hashlib.sha256(material).hexdigest()[:length]}]"


def _uuid(seed: int, source: Source, position: int) -> str:
    number = derive_seed(seed, "uuid", source.key, position)
    number = (number << 64) | derive_seed(seed, "uuid-tail", source.key, position)
    return f"[{uuid.UUID(int=number & ((1 << 128) - 1))}]"


def _typed(seed: int, source: Source, position: int) -> str:
    entity_type = str(source.attributes.get("entity_type", "SOURCE")).upper()
    return f"<{entity_type}_{position}>"


def _untyped(seed: int, source: Source, position: int) -> str:
    return f"<ENTITY_{position}>"


def _random_typed_control(seed: int, source: Source, position: int) -> str:
    return f"<{_random_chars(seed, source, position, 4)}_{position}>"


def _raw_entity(seed: int, source: Source, position: int) -> str:
    return f"[{source.attributes.get('name', source.key)}]"


_RENDERERS: dict[str, Renderer] = {
    "numeric": _numeric,
    "structured": _structured,
    "arbitrary": _arbitrary,
    "semantic": _semantic,
    "random_compact": _compact,
    "hex6": lambda s, x, p: _hex(s, x, p, 6),
    "hex32": lambda s, x, p: _hex(s, x, p, 32),
    "uuid": _uuid,
    "typed": _typed,
    "untyped": _untyped,
    "random_typed_control": _random_typed_control,
    "raw": _raw_entity,
    "random_masked": _compact,
    # The position suffix preserves uniqueness; the condition name describes the
    # controlled random payload length rather than total rendered length.
    "len1": lambda s, x, p: f"[A-{p}]",
    "len2": lambda s, x, p: f"[A7-{p}]",
    "len4": lambda s, x, p: f"[{_random_chars(s, x, p, 4)}-{p}]",
    "len8": lambda s, x, p: f"[{_random_chars(s, x, p, 8)}-{p}]",
    "len16": lambda s, x, p: f"[{_random_chars(s, x, p, 16)}-{p}]",
}


def available_conditions() -> tuple[str, ...]:
    return tuple(sorted((*_RENDERERS, "uuid_with_alias")))


def render_identifiers(
    sources: Sequence[Source],
    condition: str,
    seed: int,
    token_counter: TokenCounter,
) -> IdentifierMapping:
    if condition == "uuid_with_alias":
        display = {source.key: _uuid(seed, source, i) for i, source in enumerate(sources, 1)}
        citations = {source.key: _structured(seed, source, i) for i, source in enumerate(sources, 1)}
    else:
        try:
            renderer = _RENDERERS[condition]
        except KeyError as exc:
            choices = ", ".join(available_conditions())
            raise ValueError(f"Unknown identifier condition {condition!r}. Choose from: {choices}") from exc
        display = {source.key: renderer(seed, source, i) for i, source in enumerate(sources, 1)}
        citations = dict(display)
    if len(set(display.values())) != len(sources) or len(set(citations.values())) != len(sources):
        raise ValueError(f"Renderer {condition!r} produced duplicate identifiers")
    return IdentifierMapping(
        condition=condition,
        display_by_source=display,
        citation_by_source=citations,
        token_lengths={key: token_counter.count(value) for key, value in citations.items()},
    )

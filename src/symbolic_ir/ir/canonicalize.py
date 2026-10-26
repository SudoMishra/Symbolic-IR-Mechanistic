"""Trusted-schema canonicalization for model-facing state."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from .types import CanonicalizedExchange, IRBinding, MappingVault, ModelIR


_KIND = re.compile(r"^[A-Z][A-Z0-9]*$")


class CanonicalizationError(ValueError):
    pass


@dataclass(frozen=True)
class CanonicalizationPolicy:
    """Maps trusted application field names to symbolic handle types.

    Detection is schema-driven on purpose. Guessing identifiers or PII with a
    broad regular expression is too brittle for a production security boundary.
    """

    field_types: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.field_types:
            raise CanonicalizationError("At least one aliased field is required")
        for field_name, kind in self.field_types.items():
            if not field_name or not _KIND.fullmatch(kind):
                raise CanonicalizationError(
                    f"Invalid canonicalization rule {field_name!r}: {kind!r}"
                )


def _walk_aliases(
    value: Any,
    policy: CanonicalizationPolicy,
    path: str,
    found: list[tuple[str, str, str]],
) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key in policy.field_types:
                if not isinstance(child, str) or not child:
                    raise CanonicalizationError(
                        f"Aliased field {child_path} must contain a non-empty string"
                    )
                found.append((policy.field_types[key], child, child_path))
            _walk_aliases(child, policy, child_path, found)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _walk_aliases(child, policy, f"{path}[{index}]", found)


def _replace_strings(value: Any, pattern: re.Pattern[str] | None, aliases: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return pattern.sub(lambda match: aliases[match.group(0)], value) if pattern else value
    if isinstance(value, Mapping):
        return {key: _replace_strings(child, pattern, aliases) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_replace_strings(child, pattern, aliases) for child in value]
    return value


def canonicalize_request(
    *,
    request_id: str,
    instruction: str,
    state: Mapping[str, Any],
    policy: CanonicalizationPolicy,
) -> CanonicalizedExchange:
    """Create a model-safe request plus a separate privileged mapping vault."""

    if not request_id:
        raise CanonicalizationError("request_id is required for request-scoped isolation")
    if not isinstance(instruction, str) or not instruction:
        raise CanonicalizationError("instruction must be a non-empty string")

    occurrences: list[tuple[str, str, str]] = []
    _walk_aliases(state, policy, "state", occurrences)
    if not occurrences:
        raise CanonicalizationError("No configured alias fields were found in state")

    raw_kinds: dict[str, str] = {}
    for kind, raw, _ in occurrences:
        previous = raw_kinds.get(raw)
        if previous is not None and previous != kind:
            raise CanonicalizationError(
                "One raw value appears under multiple symbolic types; disambiguate the application schema"
            )
        raw_kinds[raw] = kind

    counters: dict[str, int] = {}
    handles: dict[tuple[str, str], str] = {}
    paths: dict[tuple[str, str], list[str]] = {}
    for kind, raw, path in occurrences:
        key = (kind, raw)
        if key not in handles:
            counters[kind] = counters.get(kind, 0) + 1
            handles[key] = f"<{kind}_{counters[kind]}>"
            paths[key] = []
        paths[key].append(path)

    bindings = tuple(
        IRBinding(
            handle=handle,
            kind=kind,
            raw_value=raw,
            source_paths=tuple(paths[(kind, raw)]),
        )
        for (kind, raw), handle in handles.items()
    )
    aliases = {binding.raw_value: binding.handle for binding in bindings}
    alternation = "|".join(re.escape(raw) for raw in sorted(aliases, key=len, reverse=True))
    pattern = re.compile(alternation) if alternation else None

    model_state = _replace_strings(state, pattern, aliases)
    model_instruction = _replace_strings(instruction, pattern, aliases)
    model_ir = ModelIR(
        request_id=request_id,
        instruction=model_instruction,
        state=model_state,
    )
    vault = MappingVault(registry_id=request_id, bindings=bindings)

    serialized = json.dumps(model_ir.to_model_payload(), sort_keys=True)
    folded_serialized = serialized.casefold()
    leaked = [raw for raw in vault.protected_values if raw.casefold() in folded_serialized]
    if leaked:
        raise CanonicalizationError("Canonicalization left protected values in the model payload")
    return CanonicalizedExchange(model_ir=model_ir, vault=vault)

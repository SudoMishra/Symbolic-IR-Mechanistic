"""Data contracts for the LLM-facing symbolic intermediate representation.

The model-visible object and the reversible mapping are deliberately separate
types.  Callers should serialize :class:`ModelIR` only; ``MappingVault`` belongs
in trusted application code outside the model context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class IRBinding:
    handle: str
    kind: str
    raw_value: str
    source_paths: tuple[str, ...]


class MappingVault:
    """Privileged, request-scoped handle mapping.

    The redacted repr helps prevent accidental notebook/log disclosure. It is
    not a security boundary; access control and encryption remain the hosting
    application's responsibility.
    """

    def __init__(self, registry_id: str, bindings: tuple[IRBinding, ...]):
        self.registry_id = registry_id
        self._bindings = bindings
        self._by_handle = {binding.handle: binding for binding in bindings}
        self._by_typed_raw = {
            (binding.kind, binding.raw_value): binding.handle for binding in bindings
        }
        if len(self._by_handle) != len(bindings):
            raise ValueError("Mapping vault contains duplicate handles")

    def __repr__(self) -> str:
        return f"MappingVault(registry_id={self.registry_id!r}, bindings=<redacted:{len(self._bindings)}>)"

    @property
    def handles(self) -> tuple[str, ...]:
        return tuple(self._by_handle)

    @property
    def protected_values(self) -> tuple[str, ...]:
        return tuple(binding.raw_value for binding in self._bindings)

    def contains(self, handle: str) -> bool:
        return handle in self._by_handle

    def kind_for_handle(self, handle: str) -> str | None:
        binding = self._by_handle.get(handle)
        return binding.kind if binding else None

    def raw_for_handle(self, handle: str) -> str:
        try:
            return self._by_handle[handle].raw_value
        except KeyError as exc:
            raise KeyError(f"Unknown symbolic handle: {handle}") from exc

    def handle_for_raw(self, raw_value: str, kind: str) -> str:
        try:
            return self._by_typed_raw[(kind, raw_value)]
        except KeyError as exc:
            raise KeyError(f"No {kind} handle for supplied raw value") from exc

    def audit_metadata(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for binding in self._bindings:
            counts[binding.kind] = counts.get(binding.kind, 0) + 1
        return {
            "registry_id": self.registry_id,
            "binding_count": len(self._bindings),
            "kind_counts": dict(sorted(counts.items())),
        }


@dataclass(frozen=True)
class ModelIR:
    """The only portion of a canonicalized request that may reach the LLM."""

    request_id: str
    instruction: str
    state: Any
    schema_version: str = "symbolic-ir-v1"
    response_contract: Mapping[str, Any] = field(default_factory=lambda: {
        "format": "json",
        "required_keys": ["answer", "references", "actions"],
        "answer": "one typed handle or a task-authorized literal",
        "references": "array of SOURCE handles",
        "actions": "array of authorized typed tool calls",
    })

    def to_model_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "instruction": self.instruction,
            "state": self.state,
            "response_contract": dict(self.response_contract),
        }


@dataclass(frozen=True)
class CanonicalizedExchange:
    model_ir: ModelIR
    vault: MappingVault


@dataclass(frozen=True)
class IRAction:
    name: str
    arguments: Mapping[str, str]


@dataclass(frozen=True)
class SymbolicResponse:
    answer: str
    references: tuple[str, ...]
    actions: tuple[IRAction, ...]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    location: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    registry_id: str
    response: SymbolicResponse | None
    issues: tuple[ValidationIssue, ...]
    output_sha256: str


@dataclass(frozen=True)
class RehydratedResponse:
    answer: str
    references: tuple[str, ...]
    actions: tuple[IRAction, ...]


@dataclass(frozen=True)
class AuditEvent:
    request_id: str
    registry_id: str
    accepted: bool
    issue_codes: tuple[str, ...]
    handles_used: tuple[str, ...]
    output_sha256: str
    binding_count: int
    kind_counts: Mapping[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "registry_id": self.registry_id,
            "accepted": self.accepted,
            "issue_codes": list(self.issue_codes),
            "handles_used": list(self.handles_used),
            "output_sha256": self.output_sha256,
            "binding_count": self.binding_count,
            "kind_counts": dict(self.kind_counts),
        }

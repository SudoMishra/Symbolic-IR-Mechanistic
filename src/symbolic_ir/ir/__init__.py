"""Production-oriented symbolic IR reference boundary."""

from .canonicalize import (
    CanonicalizationError,
    CanonicalizationPolicy,
    canonicalize_request,
)
from .protocol import (
    RehydrationError,
    ValidationPolicy,
    make_audit_event,
    rehydrate_response,
    validate_symbolic_output,
)
from .types import (
    AuditEvent,
    CanonicalizedExchange,
    IRAction,
    IRBinding,
    MappingVault,
    ModelIR,
    RehydratedResponse,
    SymbolicResponse,
    ValidationIssue,
    ValidationResult,
)

__all__ = [
    "AuditEvent",
    "CanonicalizationError",
    "CanonicalizationPolicy",
    "CanonicalizedExchange",
    "IRAction",
    "IRBinding",
    "MappingVault",
    "ModelIR",
    "RehydratedResponse",
    "RehydrationError",
    "SymbolicResponse",
    "ValidationIssue",
    "ValidationPolicy",
    "ValidationResult",
    "canonicalize_request",
    "make_audit_event",
    "rehydrate_response",
    "validate_symbolic_output",
]

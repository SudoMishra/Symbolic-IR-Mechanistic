"""Strict validation, deterministic rehydration, and privacy-safe auditing."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Mapping

from .types import (
    AuditEvent,
    IRAction,
    MappingVault,
    RehydratedResponse,
    SymbolicResponse,
    ValidationIssue,
    ValidationResult,
)


_HANDLE = re.compile(r"^<([A-Z][A-Z0-9]*)_([1-9][0-9]*)>$")
_HANDLE_CANDIDATE = re.compile(r"<[^<>\n]{1,128}>")


class RehydrationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationPolicy:
    answer_types: tuple[str, ...] = ()
    allow_literal_answer: bool = False
    reference_types: tuple[str, ...] = ("SOURCE",)
    allowed_actions: Mapping[str, Mapping[str, tuple[str, ...]]] = field(default_factory=dict)
    max_actions: int = 0
    reject_raw_exposure: bool = True


def _issue(code: str, location: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, location=location, message=message)


def _parse_strict_json(text: str) -> tuple[SymbolicResponse | None, list[ValidationIssue]]:
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None, [_issue("invalid_json", "$", "Output is not one strict JSON object")]
    if not isinstance(payload, dict):
        return None, [_issue("invalid_schema", "$", "Top-level output must be an object")]
    expected = {"answer", "references", "actions"}
    if set(payload) != expected:
        return None, [_issue(
            "invalid_schema", "$",
            f"Top-level keys must be exactly {sorted(expected)}",
        )]
    if not isinstance(payload["answer"], str):
        return None, [_issue("invalid_schema", "$.answer", "answer must be a string")]
    if not isinstance(payload["references"], list) or not all(
        isinstance(value, str) for value in payload["references"]
    ):
        return None, [_issue("invalid_schema", "$.references", "references must be strings")]
    if not isinstance(payload["actions"], list):
        return None, [_issue("invalid_schema", "$.actions", "actions must be an array")]
    actions: list[IRAction] = []
    for index, action in enumerate(payload["actions"]):
        location = f"$.actions[{index}]"
        if not isinstance(action, dict) or set(action) != {"name", "arguments"}:
            return None, [_issue(
                "invalid_schema", location,
                "Each action must contain exactly name and arguments",
            )]
        if not isinstance(action["name"], str) or not isinstance(action["arguments"], dict):
            return None, [_issue("invalid_schema", location, "Invalid action field types")]
        if not all(isinstance(key, str) and isinstance(value, str)
                   for key, value in action["arguments"].items()):
            return None, [_issue(
                "invalid_schema", f"{location}.arguments",
                "Action arguments must be string-to-string mappings",
            )]
        actions.append(IRAction(action["name"], dict(action["arguments"])))
    return SymbolicResponse(
        answer=payload["answer"],
        references=tuple(payload["references"]),
        actions=tuple(actions),
    ), []


def _check_handle(
    value: str,
    *,
    location: str,
    allowed_types: tuple[str, ...],
    vault: MappingVault,
    allow_literal: bool = False,
) -> list[ValidationIssue]:
    match = _HANDLE.fullmatch(value)
    if match is None:
        if allow_literal and not _HANDLE_CANDIDATE.search(value):
            return []
        code = "malformed_handle" if _HANDLE_CANDIDATE.search(value) else "literal_not_allowed"
        return [_issue(code, location, "Expected one complete typed symbolic handle")]
    if not vault.contains(value):
        return [_issue("unknown_handle", location, "Handle is absent from this request registry")]
    actual_type = vault.kind_for_handle(value)
    if allowed_types and actual_type not in allowed_types:
        return [_issue(
            "type_mismatch", location,
            f"Handle type {actual_type} is not allowed here",
        )]
    return []


def validate_symbolic_output(
    text: str,
    *,
    vault: MappingVault,
    policy: ValidationPolicy,
) -> ValidationResult:
    """Validate syntax, registry membership, types, leakage, and tool policy."""

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    response, issues = _parse_strict_json(text)
    if policy.reject_raw_exposure:
        folded = text.casefold()
        if any(raw.casefold() in folded for raw in vault.protected_values):
            issues.append(_issue(
                "raw_value_exposure", "$",
                "Output contains a value protected by the request registry",
            ))
    if response is not None:
        issues.extend(_check_handle(
            response.answer,
            location="$.answer",
            allowed_types=policy.answer_types,
            vault=vault,
            allow_literal=policy.allow_literal_answer,
        ))
        if len(set(response.references)) != len(response.references):
            issues.append(_issue(
                "duplicate_reference", "$.references",
                "References must not contain duplicates",
            ))
        for index, reference in enumerate(response.references):
            issues.extend(_check_handle(
                reference,
                location=f"$.references[{index}]",
                allowed_types=policy.reference_types,
                vault=vault,
            ))
        if len(response.actions) > policy.max_actions:
            issues.append(_issue(
                "action_limit_exceeded", "$.actions",
                "Output requests more actions than authorized",
            ))
        for action_index, action in enumerate(response.actions):
            location = f"$.actions[{action_index}]"
            argument_policy = policy.allowed_actions.get(action.name)
            if argument_policy is None:
                issues.append(_issue(
                    "unauthorized_action", f"{location}.name",
                    "Tool action is not authorized for this request",
                ))
                continue
            if set(action.arguments) != set(argument_policy):
                issues.append(_issue(
                    "invalid_action_arguments", f"{location}.arguments",
                    "Action argument names do not match the authorized schema",
                ))
                continue
            for name, value in action.arguments.items():
                issues.extend(_check_handle(
                    value,
                    location=f"{location}.arguments.{name}",
                    allowed_types=argument_policy[name],
                    vault=vault,
                ))

        known_or_reported = {
            candidate for candidate in _HANDLE_CANDIDATE.findall(text)
            if vault.contains(candidate)
        }
        for candidate in dict.fromkeys(_HANDLE_CANDIDATE.findall(text)):
            if candidate not in known_or_reported and not any(
                issue.code in {"unknown_handle", "malformed_handle"} and issue.location != "$"
                for issue in issues
            ):
                code = "unknown_handle" if _HANDLE.fullmatch(candidate) else "malformed_handle"
                issues.append(_issue(code, "$", "Output contains an invalid handle candidate"))

    unique_issues = tuple(dict.fromkeys(issues))
    return ValidationResult(
        accepted=response is not None and not unique_issues,
        registry_id=vault.registry_id,
        response=response,
        issues=unique_issues,
        output_sha256=digest,
    )


def rehydrate_response(result: ValidationResult, *, vault: MappingVault) -> RehydratedResponse:
    """Resolve only a previously accepted, same-request symbolic response."""

    if not result.accepted or result.response is None:
        raise RehydrationError("Refusing to rehydrate an unaccepted symbolic response")
    if result.registry_id != vault.registry_id:
        raise RehydrationError("Validation result and mapping vault belong to different requests")

    def resolve(value: str) -> str:
        return vault.raw_for_handle(value) if vault.contains(value) else value

    return RehydratedResponse(
        answer=resolve(result.response.answer),
        references=tuple(resolve(value) for value in result.response.references),
        actions=tuple(
            IRAction(action.name, {key: resolve(value) for key, value in action.arguments.items()})
            for action in result.response.actions
        ),
    )


def make_audit_event(
    *,
    request_id: str,
    result: ValidationResult,
    vault: MappingVault,
) -> AuditEvent:
    """Create an audit record containing handles and hashes, never raw values."""

    handles: list[str] = []
    if result.response is not None:
        handles.append(result.response.answer)
        handles.extend(result.response.references)
        for action in result.response.actions:
            handles.extend(action.arguments.values())
    metadata = vault.audit_metadata()
    return AuditEvent(
        request_id=request_id,
        registry_id=result.registry_id,
        accepted=result.accepted,
        issue_codes=tuple(issue.code for issue in result.issues),
        handles_used=tuple(value for value in dict.fromkeys(handles) if vault.contains(value)),
        output_sha256=result.output_sha256,
        binding_count=metadata["binding_count"],
        kind_counts=metadata["kind_counts"],
    )

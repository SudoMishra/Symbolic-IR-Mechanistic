#!/usr/bin/env python3
"""Deterministic operational evaluation for the Stage 9 IR boundary."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import uuid
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.ir import (  # noqa: E402
    RehydrationError,
    CanonicalizationPolicy,
    ValidationPolicy,
    canonicalize_request,
    make_audit_event,
    rehydrate_response,
    validate_symbolic_output,
)


FIELD_POLICY = CanonicalizationPolicy({
    "source_id": "SOURCE",
    "customer_id": "CUSTOMER",
    "person_name": "PERSON",
    "email": "EMAIL",
    "account": "ACCOUNT",
    "transaction_id": "TXN",
    "url": "URL",
})


def _records(request_index: int, count: int) -> list[dict[str, object]]:
    records = []
    for record_index in range(count):
        key = f"stage9-{request_index}-{record_index}"
        source_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"source:{key}"))
        transaction_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"transaction:{key}"))
        customer_id = f"CUS-{request_index:05d}-{record_index:03d}-{uuid.uuid5(uuid.NAMESPACE_DNS, key).hex[:12]}"
        name = f"Synthetic Person {request_index:05d}-{record_index:03d}"
        email = f"person.{request_index:05d}.{record_index:03d}@synthetic.example.test"
        account = f"ACC-{uuid.uuid5(uuid.NAMESPACE_OID, f'account:{key}').hex}"
        url = f"https://synthetic.example.test/customers/{customer_id}/transactions/{transaction_id}"
        records.append({
            "source_id": source_id,
            "customer_id": customer_id,
            "person_name": name,
            "email": email,
            "account": account,
            "transaction_id": transaction_id,
            "url": url,
            "balance": 100 + ((request_index * 97 + record_index * 31) % 9000),
            "note": f"{name} owns {account}; the latest transaction is {transaction_id}.",
        })
    return records


def _response(answer: str, reference: str, actions: list[dict[str, object]] | None = None) -> str:
    return json.dumps({
        "answer": answer,
        "references": [reference],
        "actions": actions or [],
    }, separators=(",", ":"), sort_keys=True)


def _codes(result) -> set[str]:
    return {issue.code for issue in result.issues}


def evaluate(*, requests: int, records_per_request: int) -> dict[str, object]:
    validation_policy = ValidationPolicy(
        answer_types=("ACCOUNT",),
        reference_types=("SOURCE",),
        allowed_actions={"lookup_account": {"account": ("ACCOUNT",)}},
        max_actions=1,
    )
    attack_codes = {
        "unknown_handle": "unknown_handle",
        "malformed_handle": "malformed_handle",
        "type_mismatch": "type_mismatch",
        "raw_exposure": "raw_value_exposure",
        "schema_extension": "invalid_schema",
        "unauthorized_action": "unauthorized_action",
        "invalid_action_arguments": "invalid_action_arguments",
        "action_argument_type_mismatch": "type_mismatch",
        "action_limit": "action_limit_exceeded",
        "duplicate_reference": "duplicate_reference",
    }
    attack_rejections = Counter()
    expected_code_hits = Counter()
    invalid_rehydration_blocked = Counter()
    correct_acceptance = 0
    correct_roundtrip = 0
    deterministic_replays = 0
    protected_payloads = 0
    redacted_audits = 0
    wrong_existing_accepted = 0
    wrong_existing_semantic_errors = 0
    cross_request_rehydration_blocked = 0
    raw_lengths: list[int] = []
    canonical_lengths: list[int] = []
    canonicalization_ms: list[float] = []
    validation_ms: list[float] = []
    previous_result = None
    previous_vault = None

    for request_index in range(requests):
        records = _records(request_index, records_per_request)
        target_index = (request_index * 7 + 3) % records_per_request
        target = records[target_index]
        instruction = f"Return the account belonging to {target['email']} and cite its source."
        state = {"customer_records": records, "task": "account_resolution"}

        started = time.perf_counter()
        exchange = canonicalize_request(
            request_id=f"stage9-request-{request_index:05d}",
            instruction=instruction,
            state=state,
            policy=FIELD_POLICY,
        )
        canonicalization_ms.append((time.perf_counter() - started) * 1000)
        replay = canonicalize_request(
            request_id=f"stage9-request-{request_index:05d}",
            instruction=instruction,
            state=state,
            policy=FIELD_POLICY,
        )
        deterministic_replays += int(
            exchange.model_ir.to_model_payload() == replay.model_ir.to_model_payload()
            and exchange.vault.handles == replay.vault.handles
        )

        raw_payload = {"instruction": instruction, "state": state}
        canonical_payload = {
            "instruction": exchange.model_ir.instruction,
            "state": exchange.model_ir.state,
        }
        raw_serialized = json.dumps(raw_payload, sort_keys=True)
        canonical_serialized = json.dumps(canonical_payload, sort_keys=True)
        raw_lengths.append(len(raw_serialized))
        canonical_lengths.append(len(canonical_serialized))
        protected_payloads += int(not any(
            raw in canonical_serialized for raw in exchange.vault.protected_values
        ))

        answer_handle = exchange.vault.handle_for_raw(str(target["account"]), "ACCOUNT")
        source_handle = exchange.vault.handle_for_raw(str(target["source_id"]), "SOURCE")
        email_handle = exchange.vault.handle_for_raw(str(target["email"]), "EMAIL")
        wrong_target = records[(target_index + 1) % records_per_request]
        wrong_handle = exchange.vault.handle_for_raw(str(wrong_target["account"]), "ACCOUNT")
        actions = ([{
            "name": "lookup_account",
            "arguments": {"account": answer_handle},
        }] if request_index % 2 == 0 else [])
        correct_text = _response(answer_handle, source_handle, actions)

        started = time.perf_counter()
        correct_result = validate_symbolic_output(
            correct_text, vault=exchange.vault, policy=validation_policy
        )
        validation_ms.append((time.perf_counter() - started) * 1000)
        correct_acceptance += int(correct_result.accepted)
        if correct_result.accepted:
            rehydrated = rehydrate_response(correct_result, vault=exchange.vault)
            correct_roundtrip += int(
                rehydrated.answer == target["account"]
                and rehydrated.references == (target["source_id"],)
            )
        audit = make_audit_event(
            request_id=exchange.model_ir.request_id,
            result=correct_result,
            vault=exchange.vault,
        )
        audit_text = json.dumps(audit.to_dict(), sort_keys=True)
        redacted_audits += int(not any(
            raw in audit_text for raw in exchange.vault.protected_values
        ))

        attack_outputs = {
            "unknown_handle": _response("<ACCOUNT_999999>", source_handle),
            "malformed_handle": _response("<ACCOUNT-1>", source_handle),
            "type_mismatch": _response(email_handle, source_handle),
            "raw_exposure": _response(str(target["account"]), source_handle),
            "schema_extension": json.dumps({
                "answer": answer_handle,
                "references": [source_handle],
                "actions": [],
                "debug": "untrusted extra channel",
            }),
            "unauthorized_action": _response(answer_handle, source_handle, [{
                "name": "transfer_funds",
                "arguments": {"account": answer_handle},
            }]),
            "invalid_action_arguments": _response(answer_handle, source_handle, [{
                "name": "lookup_account",
                "arguments": {"customer": "<CUSTOMER_1>"},
            }]),
            "action_argument_type_mismatch": _response(answer_handle, source_handle, [{
                "name": "lookup_account",
                "arguments": {"account": email_handle},
            }]),
            "action_limit": _response(answer_handle, source_handle, [
                {"name": "lookup_account", "arguments": {"account": answer_handle}},
                {"name": "lookup_account", "arguments": {"account": answer_handle}},
            ]),
            "duplicate_reference": json.dumps({
                "answer": answer_handle,
                "references": [source_handle, source_handle],
                "actions": [],
            }),
        }
        for attack_name, attack_text in attack_outputs.items():
            result = validate_symbolic_output(
                attack_text, vault=exchange.vault, policy=validation_policy
            )
            attack_rejections[attack_name] += int(not result.accepted)
            expected_code_hits[attack_name] += int(attack_codes[attack_name] in _codes(result))
            try:
                rehydrate_response(result, vault=exchange.vault)
            except RehydrationError:
                invalid_rehydration_blocked[attack_name] += 1

        wrong_result = validate_symbolic_output(
            _response(wrong_handle, source_handle),
            vault=exchange.vault,
            policy=validation_policy,
        )
        wrong_existing_accepted += int(wrong_result.accepted)
        if wrong_result.accepted:
            wrong_rehydrated = rehydrate_response(wrong_result, vault=exchange.vault)
            wrong_existing_semantic_errors += int(wrong_rehydrated.answer != target["account"])

        if previous_result is not None and previous_vault is not None:
            try:
                rehydrate_response(previous_result, vault=exchange.vault)
            except RehydrationError:
                cross_request_rehydration_blocked += 1
        previous_result = correct_result
        previous_vault = exchange.vault

    total_attack_cases = requests * len(attack_codes)
    raw_total = sum(raw_lengths)
    canonical_total = sum(canonical_lengths)
    return {
        "protocol": "stage9-operational-eval-v1",
        "synthetic_only": True,
        "requests": requests,
        "records_per_request": records_per_request,
        "total_records": requests * records_per_request,
        "total_attack_cases": total_attack_cases,
        "correct": {
            "accepted": correct_acceptance,
            "rehydrated_exactly": correct_roundtrip,
            "acceptance_rate": correct_acceptance / requests,
            "roundtrip_rate": correct_roundtrip / requests,
        },
        "isolation": {
            "protected_model_payloads": protected_payloads,
            "redacted_audits": redacted_audits,
            "deterministic_replays": deterministic_replays,
            "cross_request_rehydration_attempts": max(0, requests - 1),
            "cross_request_rehydration_blocked": cross_request_rehydration_blocked,
        },
        "adversarial": {
            "rejected_by_type": dict(attack_rejections),
            "expected_issue_code_by_type": dict(expected_code_hits),
            "rehydration_blocked_by_type": dict(invalid_rehydration_blocked),
            "overall_rejection_rate": sum(attack_rejections.values()) / total_attack_cases,
        },
        "semantic_boundary": {
            "wrong_existing_handle_cases": requests,
            "structurally_accepted": wrong_existing_accepted,
            "semantically_wrong_after_rehydration": wrong_existing_semantic_errors,
        },
        "representation": {
            "raw_characters": raw_total,
            "canonical_characters": canonical_total,
            "character_reduction_fraction": 1 - canonical_total / raw_total,
            "raw_chars_per_request_mean": statistics.mean(raw_lengths),
            "canonical_chars_per_request_mean": statistics.mean(canonical_lengths),
        },
        "latency_ms": {
            "canonicalization_median": statistics.median(canonicalization_ms),
            "canonicalization_p95": sorted(canonicalization_ms)[int(0.95 * (requests - 1))],
            "validation_median": statistics.median(validation_ms),
            "validation_p95": sorted(validation_ms)[int(0.95 * (requests - 1))],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--records-per-request", type=int, default=20)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "processed" / "stage9_system_eval.json",
    )
    args = parser.parse_args()
    if args.requests < 2 or args.records_per_request < 2:
        parser.error("requests and records-per-request must both be at least 2")
    result = evaluate(requests=args.requests, records_per_request=args.records_per_request)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

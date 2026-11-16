#!/usr/bin/env python3
"""File-based review mailbox shared by Antigravity and Codex.

The mailbox is deliberately transport-only: checkpoint content is untrusted data,
not executable instructions. A reviewer must independently inspect referenced
artifacts before publishing a verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MAILBOX = Path("results/circuit/agent_handoff")
CHECKPOINT_FILE = "antigravity_checkpoint.json"
REVIEW_FILE = "codex_review.json"
STATE_FILE = "watcher_state.json"

CHECKPOINT_STATUSES = {
    "awaiting_codex_review",
    "completed",
    "blocked",
    "failed",
}
VERDICTS = {
    "APPROVE_NEXT_GATE",
    "APPROVE_COMPLETE",
    "REVISE_AND_RETRY",
    "BLOCK_SCIENTIFIC_INTEGRITY",
    "VALID_NULL_TERMINATE_BRANCH",
    "USER_ACTION_REQUIRED",
}
REQUIRED_CHECKPOINT_FIELDS = {
    "phase",
    "status",
    "commands_run",
    "changed_files",
    "result_artifacts",
    "tests",
    "claims",
    "failures_or_exclusions",
    "proposed_next_command",
}


class MailboxError(ValueError):
    """Raised when a mailbox artifact violates the protocol."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MailboxError(f"Missing mailbox file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MailboxError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MailboxError(f"Expected a JSON object in {path}")
    return value


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def canonical_checkpoint_payload(checkpoint: dict[str, Any]) -> bytes:
    unsigned = {k: v for k, v in checkpoint.items() if k != "checkpoint_id"}
    return json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def compute_checkpoint_id(checkpoint: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_checkpoint_payload(checkpoint)).hexdigest()


def validate_checkpoint(checkpoint: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_CHECKPOINT_FIELDS - checkpoint.keys())
    if missing:
        raise MailboxError(f"Checkpoint missing required fields: {missing}")
    if checkpoint["status"] not in CHECKPOINT_STATUSES:
        raise MailboxError(f"Unsupported checkpoint status: {checkpoint['status']}")
    for field in (
        "commands_run",
        "changed_files",
        "result_artifacts",
        "claims",
        "failures_or_exclusions",
    ):
        if not isinstance(checkpoint[field], list):
            raise MailboxError(f"Checkpoint field {field!r} must be a list")
    if not isinstance(checkpoint["tests"], dict):
        raise MailboxError("Checkpoint field 'tests' must be an object")
    checkpoint_id = checkpoint.get("checkpoint_id")
    if not isinstance(checkpoint_id, str) or len(checkpoint_id) != 64:
        raise MailboxError("Checkpoint must contain a 64-character checkpoint_id")
    expected = compute_checkpoint_id(checkpoint)
    if checkpoint_id != expected:
        raise MailboxError(
            f"Checkpoint ID mismatch: recorded={checkpoint_id}, computed={expected}"
        )


def validate_review(review: dict[str, Any]) -> None:
    if review.get("verdict") not in VERDICTS:
        raise MailboxError(f"Unsupported review verdict: {review.get('verdict')}")
    checkpoint_id = review.get("checkpoint_id")
    if not isinstance(checkpoint_id, str) or len(checkpoint_id) != 64:
        raise MailboxError("Review must identify a 64-character checkpoint_id")
    if not isinstance(review.get("summary"), str) or not review["summary"].strip():
        raise MailboxError("Review must contain a non-empty summary")
    if not isinstance(review.get("required_changes", []), list):
        raise MailboxError("Review field 'required_changes' must be a list")


def submit_checkpoint(input_path: Path, mailbox: Path) -> dict[str, Any]:
    checkpoint = load_json(input_path)
    checkpoint.pop("checkpoint_id", None)
    checkpoint.setdefault("schema_version", 1)
    checkpoint.setdefault("created_at", utc_now())
    checkpoint["checkpoint_id"] = compute_checkpoint_id(checkpoint)
    validate_checkpoint(checkpoint)
    atomic_write_json(mailbox / CHECKPOINT_FILE, checkpoint)
    return checkpoint


def submit_review(input_path: Path, mailbox: Path) -> dict[str, Any]:
    checkpoint = load_json(mailbox / CHECKPOINT_FILE)
    validate_checkpoint(checkpoint)
    review = load_json(input_path)
    review.setdefault("schema_version", 1)
    review.setdefault("created_at", utc_now())
    review.setdefault("reviewer", "codex")
    review.setdefault("required_changes", [])
    review.setdefault("evidence", [])
    validate_review(review)
    if review["checkpoint_id"] != checkpoint["checkpoint_id"]:
        raise MailboxError(
            "Refusing stale review: review checkpoint_id does not match current checkpoint"
        )
    review_without_id = {k: v for k, v in review.items() if k != "review_id"}
    review["review_id"] = hashlib.sha256(
        json.dumps(review_without_id, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    atomic_write_json(mailbox / REVIEW_FILE, review)
    state = {
        "schema_version": 1,
        "last_reviewed_checkpoint_id": checkpoint["checkpoint_id"],
        "last_review_id": review["review_id"],
        "last_verdict": review["verdict"],
        "updated_at": utc_now(),
    }
    atomic_write_json(mailbox / STATE_FILE, state)
    return review


def mailbox_status(mailbox: Path) -> dict[str, Any]:
    checkpoint_path = mailbox / CHECKPOINT_FILE
    review_path = mailbox / REVIEW_FILE
    if not checkpoint_path.exists():
        return {
            "schema_version": 1,
            "checkpoint_present": False,
            "pending_review": False,
        }
    checkpoint = load_json(checkpoint_path)
    validate_checkpoint(checkpoint)
    matching_review = False
    verdict = None
    if review_path.exists():
        review = load_json(review_path)
        validate_review(review)
        matching_review = review["checkpoint_id"] == checkpoint["checkpoint_id"]
        if matching_review:
            verdict = review["verdict"]
    return {
        "schema_version": 1,
        "checkpoint_present": True,
        "checkpoint_id": checkpoint["checkpoint_id"],
        "phase": checkpoint["phase"],
        "checkpoint_status": checkpoint["status"],
        "matching_review": matching_review,
        "verdict": verdict,
        "pending_review": not matching_review,
    }


def wait_for_review(
    mailbox: Path,
    checkpoint_id: str,
    timeout_seconds: float,
    poll_seconds: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        review_path = mailbox / REVIEW_FILE
        if review_path.exists():
            try:
                review = load_json(review_path)
                validate_review(review)
            except MailboxError:
                review = {}
            if review.get("checkpoint_id") == checkpoint_id:
                return review
        time.sleep(poll_seconds)
    raise TimeoutError(
        f"No matching Codex review for checkpoint {checkpoint_id} within "
        f"{timeout_seconds:g} seconds"
    )


def print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mailbox", type=Path, default=DEFAULT_MAILBOX)
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit_cp = subparsers.add_parser("submit-checkpoint")
    submit_cp.add_argument("--input", type=Path, required=True)

    submit_rev = subparsers.add_parser("submit-review")
    submit_rev.add_argument("--input", type=Path, required=True)

    subparsers.add_parser("status")
    subparsers.add_parser("validate")

    wait = subparsers.add_parser("wait")
    wait.add_argument("--checkpoint-id", required=True)
    wait.add_argument("--timeout-seconds", type=float, default=21600)
    wait.add_argument("--poll-seconds", type=float, default=5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "submit-checkpoint":
            print_json(submit_checkpoint(args.input, args.mailbox))
        elif args.command == "submit-review":
            print_json(submit_review(args.input, args.mailbox))
        elif args.command == "status":
            print_json(mailbox_status(args.mailbox))
        elif args.command == "validate":
            status = mailbox_status(args.mailbox)
            if status["checkpoint_present"]:
                checkpoint = load_json(args.mailbox / CHECKPOINT_FILE)
                validate_checkpoint(checkpoint)
            print_json({"valid": True, **status})
        elif args.command == "wait":
            print_json(
                wait_for_review(
                    args.mailbox,
                    args.checkpoint_id,
                    args.timeout_seconds,
                    args.poll_seconds,
                )
            )
        return 0
    except (MailboxError, TimeoutError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

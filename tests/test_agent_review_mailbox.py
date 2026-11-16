import json
from pathlib import Path

import pytest

from scripts.agent_review_mailbox import (
    MailboxError,
    atomic_write_json,
    compute_checkpoint_id,
    mailbox_status,
    submit_checkpoint,
    submit_review,
    validate_checkpoint,
    wait_for_review,
)


def checkpoint_draft() -> dict:
    return {
        "phase": "PHASE_1",
        "status": "awaiting_codex_review",
        "commands_run": ["pytest tests/test_example.py"],
        "changed_files": ["scripts/example.py"],
        "result_artifacts": [],
        "tests": {"passed": 1, "failed": 0},
        "claims": [],
        "failures_or_exclusions": [],
        "proposed_next_command": "python scripts/example.py",
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_submit_checkpoint_is_hashed_and_pending(tmp_path: Path):
    draft = tmp_path / "draft.json"
    mailbox = tmp_path / "mailbox"
    write_json(draft, checkpoint_draft())

    checkpoint = submit_checkpoint(draft, mailbox)

    assert checkpoint["checkpoint_id"] == compute_checkpoint_id(checkpoint)
    assert mailbox_status(mailbox)["pending_review"] is True


def test_tampered_checkpoint_is_rejected(tmp_path: Path):
    checkpoint = checkpoint_draft()
    checkpoint["created_at"] = "2026-01-01T00:00:00+00:00"
    checkpoint["checkpoint_id"] = compute_checkpoint_id(checkpoint)
    checkpoint["phase"] = "TAMPERED"

    with pytest.raises(MailboxError, match="Checkpoint ID mismatch"):
        validate_checkpoint(checkpoint)


def test_stale_review_does_not_satisfy_new_checkpoint(tmp_path: Path):
    mailbox = tmp_path / "mailbox"
    mailbox.mkdir()
    draft = tmp_path / "draft.json"
    write_json(draft, checkpoint_draft())
    submit_checkpoint(draft, mailbox)
    atomic_write_json(
        mailbox / "codex_review.json",
        {
            "checkpoint_id": "0" * 64,
            "verdict": "APPROVE_NEXT_GATE",
            "summary": "Old review",
            "required_changes": [],
        },
    )

    status = mailbox_status(mailbox)

    assert status["matching_review"] is False
    assert status["pending_review"] is True


def test_submit_review_requires_current_checkpoint(tmp_path: Path):
    mailbox = tmp_path / "mailbox"
    mailbox.mkdir()
    draft = tmp_path / "draft.json"
    write_json(draft, checkpoint_draft())
    submit_checkpoint(draft, mailbox)
    review_draft = tmp_path / "review.json"
    write_json(
        review_draft,
        {
            "checkpoint_id": "f" * 64,
            "verdict": "APPROVE_NEXT_GATE",
            "summary": "Looks good",
        },
    )

    with pytest.raises(MailboxError, match="Refusing stale review"):
        submit_review(review_draft, mailbox)


def test_matching_review_is_returned_to_waiter(tmp_path: Path):
    mailbox = tmp_path / "mailbox"
    mailbox.mkdir()
    draft = tmp_path / "draft.json"
    write_json(draft, checkpoint_draft())
    checkpoint = submit_checkpoint(draft, mailbox)
    review_draft = tmp_path / "review.json"
    write_json(
        review_draft,
        {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "verdict": "REVISE_AND_RETRY",
            "summary": "Add a semantic regression test",
            "required_changes": ["Add the missing test"],
        },
    )
    submitted = submit_review(review_draft, mailbox)

    observed = wait_for_review(mailbox, checkpoint["checkpoint_id"], 0.2, 0.01)

    assert observed["review_id"] == submitted["review_id"]
    assert mailbox_status(mailbox)["pending_review"] is False

"""Unit tests for Phase 6 Behavioral Bridge evaluation metrics and error taxonomy."""

from __future__ import annotations

import pytest
from scripts.run_behavioral_bridge import score_behavioral_response


def test_score_behavioral_response_clean():
    """Verify clean response scores perfect EM, cites gold, and has no error."""
    text = "ANSWER: 42\nCITATIONS: [S1]"
    expected_ans = "42"
    gold_label = "[S1]"
    cf_label = "[S2]"
    allowed = ["[S1]", "[S2]", "[S3]"]

    res = score_behavioral_response(text, expected_ans, gold_label, cf_label, allowed)

    assert res["answer_em"] is True
    assert res["cites_gold"] is True
    assert res["cites_counterfactual"] is False
    assert res["selective_dissociation"] is False
    assert res["error_type"] == "none"
    assert res["citation_precision"] == 1.0
    assert res["citation_recall"] == 1.0


def test_score_behavioral_response_selective_dissociation():
    """Verify that preserving answer EM while switching citation to counterfactual triggers selective_dissociation."""
    text = "ANSWER: 42\nCITATIONS: [S2]"
    expected_ans = "42"
    gold_label = "[S1]"
    cf_label = "[S2]"
    allowed = ["[S1]", "[S2]", "[S3]"]

    res = score_behavioral_response(text, expected_ans, gold_label, cf_label, allowed)

    assert res["answer_em"] is True
    assert res["cites_gold"] is False
    assert res["cites_counterfactual"] is True
    assert res["selective_dissociation"] is True
    assert res["error_type"] == "counterfactual_cited"


def test_score_behavioral_response_omitted_and_wrong_source():
    """Verify omitted citation and distractor citation categorization."""
    expected_ans = "42"
    gold_label = "[S1]"
    cf_label = "[S2]"
    allowed = ["[S1]", "[S2]", "[S3]"]

    # Omitted citation
    text_omitted = "ANSWER: 42\nCITATIONS: "
    res_omitted = score_behavioral_response(text_omitted, expected_ans, gold_label, cf_label, allowed)
    assert res_omitted["answer_em"] is True
    assert res_omitted["error_type"] == "omitted_citation"

    # Wrong distractor source
    text_wrong = "ANSWER: 42\nCITATIONS: [S3]"
    res_wrong = score_behavioral_response(text_wrong, expected_ans, gold_label, cf_label, allowed)
    assert res_wrong["answer_em"] is True
    assert res_wrong["error_type"] == "wrong_source"


def test_score_behavioral_response_answer_incorrect():
    """Verify wrong answer detection."""
    text = "ANSWER: 999\nCITATIONS: [S1]"
    expected_ans = "42"
    gold_label = "[S1]"
    cf_label = "[S2]"
    allowed = ["[S1]", "[S2]", "[S3]"]

    res = score_behavioral_response(text, expected_ans, gold_label, cf_label, allowed)
    assert res["answer_em"] is False
    assert res["cites_gold"] is True
    assert res["error_type"] == "answer_incorrect"

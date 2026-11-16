"""Phase 1: Sequence 2R Semantic Repair Regression Tests.

Verifies:
1. Distinguishing-token logit position (target_positions[d] - 1).
2. One-based scientific layer convention (Layer L -> layers[L - 1]).
3. Order-permutation estimand (clean vs fixed-distractor contrast, preserved pairings).
4. Question-swap grounding (entailed answer, single gold supporting source, or explicit ineligibility).
5. Semantic position alignment (handles length differences without dropping examples).
6. Autoregressive causal interpretation (handle identity vs post-evidence binding vs output routing).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
import torch
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def qwen_tokenizer():
    return AutoTokenizer.from_pretrained("models/qwen2.5-1.5b-instruct-hf")


def test_distinguishing_token_logit_position(qwen_tokenizer):
    """Test 1: Distinguishing token evaluation must occur at target_positions[d] - 1."""
    from scripts.run_computation_vs_transport import (
        find_first_distinguishing_index,
        extract_citation_eval_positions,
    )

    test_cases = [
        # (clean_label, donor_label, expected_d, condition_name)
        ("[S7]", "[S1]", 1, "structured"),
        ("[1]", "[2]", 1, "structured_single_digit"),
        ("[7XD1]", "[ZGWN]", 0, "compact"),
        ("[f1b72100-79db-7ffb-c06b-7e95aabffe54]", "[1399fd0a-86af-c1c0-ce3f-a63b40bd9382]", 0, "uuid"),
    ]

    for clean_lbl, donor_lbl, expected_d, cond in test_cases:
        clean_toks = qwen_tokenizer.encode(clean_lbl, add_special_tokens=False)
        donor_toks = qwen_tokenizer.encode(donor_lbl, add_special_tokens=False)

        d = find_first_distinguishing_index(clean_toks, donor_toks)
        assert d == expected_d, f"Condition {cond}: expected d={expected_d}, got {d}"

        # Test prompt structure
        prompt = "Sources:\n[S1] Fact.\nQuestion: What fact?\n"
        answer = "Fact"
        eval_pos_clean = extract_citation_eval_positions(qwen_tokenizer, prompt, answer, clean_lbl, d)
        eval_pos_donor = extract_citation_eval_positions(qwen_tokenizer, prompt, answer, donor_lbl, d)

        # Distinguishing token is at target_positions[d]
        # The predicting logit position must be target_positions[d] - 1
        assert eval_pos_clean["eval_pos"] == eval_pos_clean["target_positions"][d] - 1
        assert eval_pos_donor["eval_pos"] == eval_pos_donor["target_positions"][d] - 1

        # Verify that for [S7] vs [S1], eval_pos is NOT target_positions[0] - 1
        if clean_lbl == "[S7]":
            assert eval_pos_clean["eval_pos"] == eval_pos_clean["target_positions"][1] - 1
            assert eval_pos_clean["eval_pos"] != eval_pos_clean["target_positions"][0] - 1


def test_one_based_scientific_layer_convention():
    """Test 2: Scientific layer L must map to stack index L - 1 and validate range."""
    from scripts.run_computation_vs_transport import resolve_layer_indices

    # Qwen 2.5 1.5B has 28 layers
    num_total_layers = 28

    # Valid layer 14 -> index 13
    l14 = resolve_layer_indices(14, num_total_layers)
    assert l14["layer_1based"] == 14
    assert l14["layer_0based"] == 13
    assert l14["stack_idx"] == 13

    # Valid layer 20 -> index 19
    l20 = resolve_layer_indices(20, num_total_layers)
    assert l20["layer_1based"] == 20
    assert l20["layer_0based"] == 19

    # Valid layer 24 -> index 23
    l24 = resolve_layer_indices(24, num_total_layers)
    assert l24["layer_1based"] == 24
    assert l24["layer_0based"] == 23

    # Boundary cases
    l1 = resolve_layer_indices(1, num_total_layers)
    assert l1["layer_0based"] == 0

    l28 = resolve_layer_indices(28, num_total_layers)
    assert l28["layer_0based"] == 27

    # Invalid cases must raise ValueError
    with pytest.raises(ValueError, match="out of range"):
        resolve_layer_indices(0, num_total_layers)

    with pytest.raises(ValueError, match="out of range"):
        resolve_layer_indices(-1, num_total_layers)

    with pytest.raises(ValueError, match="out of range"):
        resolve_layer_indices(29, num_total_layers)


def test_order_permutation_contrast_and_invariants(qwen_tokenizer):
    """Test 3: Order permutation must preserve clean-vs-distractor contrast and pairing invariants."""
    from scripts.run_computation_vs_transport import (
        build_repaired_corruptions,
        create_token_counter,
    )
    from symbolic_ir.schema import CanonicalExample, Source

    # Synthetic example
    sources = [
        Source(f"src_{i}", f"Registry entry {i} for dept {chr(65+i)}.")
        for i in range(10)
    ]
    ex = CanonicalExample(
        example_id="test_ex_001",
        seed=42,
        task_type="temporal",
        sources=tuple(sources),
        relevant_sources=("src_3",),
        question="Which dept has entry 3?",
        answer="D",
        entities={},
    )
    counter = create_token_counter({"type": "regex"})
    case = {
        "example_id": ex.example_id,
        "task_type": "temporal",
        "condition": "structured",
        "clean_label": "[S4]",
        "swapped_label": "[S1]",
        "relevant_source_key": "src_3",
        "distractor_source_key": "src_0",
        "sources": [{"key": s.key, "text": s.text} for s in sources],
    }

    corruptions = build_repaired_corruptions(case, counter, qwen_tokenizer)
    assert "order_perm" in corruptions
    perm = corruptions["order_perm"]

    # Invariant: pairing between relevant_source_key and its display handle is preserved
    assert perm["invariants"]["content_label_pairing_preserved"] is True
    assert perm["invariants"]["passage_slot_changed"] is True

    # Contrast tokens must be clean distinguishing token vs distractor distinguishing token
    # NOT clean vs clean!
    assert perm["clean_tok"] != perm["distractor_tok"], "Order perm contrast must compare distinct tokens"
    assert perm["clean_target_label"] == "[S4]"
    assert perm["distractor_target_label"] == "[S1]"


def test_question_swap_grounding(qwen_tokenizer):
    """Test 4: Question swap must have an entailed answer and single gold supporting source."""
    from scripts.run_computation_vs_transport import (
        build_repaired_corruptions,
        create_token_counter,
    )
    from symbolic_ir.schema import Source

    # Case with valid distractor factual sentence
    sources_valid = [
        {"key": "distractor-8", "text": "An unrelated registry entry reports reference value 4530 for department I in cycle 11. Notes follow."},
        {"key": "anchor", "text": "The intake meeting occurred on day 6 of the project."},
    ]
    case_valid = {
        "example_id": "test_qswap_valid",
        "task_type": "temporal",
        "condition": "structured",
        "clean_label": "[S2]",
        "swapped_label": "[S1]",
        "relevant_source_key": "anchor",
        "distractor_source_key": "distractor-8",
        "sources": sources_valid,
    }
    counter = create_token_counter({"type": "regex"})
    corrs_valid = build_repaired_corruptions(case_valid, counter, qwen_tokenizer)
    qswap = corrs_valid["question_swap"]

    assert qswap["is_eligible"] is True
    assert qswap["gold_source_key"] == "distractor-8"
    assert "4530" in qswap["answer"]
    assert "department I in cycle 11" in qswap["prompt"]

    # Case with ungroundable sources -> must mark ineligible, not invent text
    sources_invalid = [
        {"key": "distractor-x", "text": "No parseable pattern here without department or value."},
        {"key": "anchor", "text": "The intake meeting occurred on day 6 of the project."},
    ]
    case_invalid = {
        "example_id": "test_qswap_invalid",
        "task_type": "temporal",
        "condition": "structured",
        "clean_label": "[S2]",
        "swapped_label": "[S1]",
        "relevant_source_key": "anchor",
        "distractor_source_key": "distractor-x",
        "sources": sources_invalid,
    }
    corrs_invalid = build_repaired_corruptions(case_invalid, counter, qwen_tokenizer)
    assert corrs_invalid["question_swap"]["is_eligible"] is False
    assert "reason" in corrs_invalid["question_swap"]


def test_semantic_position_alignment():
    """Test 5: Unequal length spans must be aligned without dropping examples, supporting 2D tensors."""
    from scripts.run_computation_vs_transport import align_activation_spans

    # Clean span: 5 tokens, Donor span: 4 tokens
    d_model = 1536
    clean_pos = [10, 11, 12, 13, 14]  # len 5
    donor_pos = [20, 21, 22, 23]      # len 4

    # 2D tensor as recorded from primary[0, pos, :]
    donor_act_2d = torch.randn(len(donor_pos), d_model)
    aligned_act_2d, diag_2d = align_activation_spans(clean_pos, donor_pos, donor_act_2d)

    assert aligned_act_2d.shape == (len(clean_pos), d_model)
    assert diag_2d["clean_len"] == 5
    assert diag_2d["donor_len"] == 4
    assert diag_2d["aligned"] is True
    assert diag_2d["method"] in ["linear_interpolation", "endpoint_aligned"]

    # 3D tensor support
    donor_act_3d = torch.randn(1, len(donor_pos), d_model)
    aligned_act_3d, diag_3d = align_activation_spans(clean_pos, donor_pos, donor_act_3d)
    assert aligned_act_3d.shape == (1, len(clean_pos), d_model)
    assert diag_3d["aligned"] is True


def test_autoregressive_causal_position_distinction(qwen_tokenizer):
    """Test 6: Verify causal distinction between handle identity, post-evidence, and output routing."""
    from scripts.run_computation_vs_transport import locate_semantic_positions

    prompt = (
        "SOURCES\n"
        "[S7] The intake meeting occurred on day 6 of the project. Administrative details follow.\n"
        "[S1] An unrelated registry entry reports reference value 4530.\n\n"
        "QUESTION\nOn which day did the intake meeting occur?\n"
    )
    answer = "day 6"
    citation = "[S7]"

    positions = locate_semantic_positions(
        tokenizer=qwen_tokenizer,
        prompt=prompt,
        answer=answer,
        citation_label=citation,
        relevant_handle="[S7]",
        evidence_substring="The intake meeting occurred on day 6 of the project.",
    )

    # 1. Handle identity position precedes evidence in token order
    handle_pos = positions["pos_source_handle"]
    evidence_pos = positions["pos_evidence"]
    assert max(handle_pos) < min(evidence_pos), "Source handle must precede evidence in prompt"
    assert positions["role_map"]["pos_source_handle"] == "handle_identity"

    # 2. Post-evidence position occurs after evidence has entered context
    post_ev_pos = positions["pos_post_evidence"]
    assert max(post_ev_pos) >= max(evidence_pos), "Post-evidence position must be at or after end of evidence"
    assert positions["role_map"]["pos_post_evidence"] == "binding_construction"

    # 3. Citation position occurs in output continuation
    cit_pos = positions["pos_citation"]
    ans_pos = positions["pos_answer"]
    assert min(cit_pos) > max(ans_pos), "Citation predicting position must follow answer in output"
    assert positions["role_map"]["pos_citation"] == "output_routing"

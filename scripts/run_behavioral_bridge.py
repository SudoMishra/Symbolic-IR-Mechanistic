#!/usr/bin/env python3
"""Phase 6: Behavioral Bridge and Free Generation Evaluation.

Evaluates free autoregressive generation under clean, corrupt, and causally intervened conditions:
1. Clean Prompt Baseline: measures baseline answer accuracy and citation correctness.
2. Swapped Prompt Baseline: measures counterfactual behavior under full prompt swap.
3. Causal Intervention (Head Subset or Subspace Projection): evaluates whether causal patching
   shifts citation generation toward the counterfactual target WHILE preserving factual answer accuracy.
4. Error Taxonomy: tracks wrong-source, omitted-citation, and spurious-citation rates.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.audit_component_hooks import get_layer_components  # noqa: E402
from scripts.run_causal_subspace import SubspaceProjectionPatcher  # noqa: E402
from scripts.run_computation_vs_transport import (  # noqa: E402
    align_activation_spans,
    find_first_distinguishing_index,
    locate_semantic_positions,
    resolve_layer_indices,
)
from scripts.run_head_decomposition import (  # noqa: E402
    HeadSubsetPatcher,
    MultiHeadActivationRecorder,
)
from scripts.run_stage6 import find_transformer_stack  # noqa: E402
from scripts.run_stage7 import format_prompt, load_model, resolve  # noqa: E402
from symbolic_ir.config import load_config  # noqa: E402
from symbolic_ir.evaluation.answer import answer_exact_match  # noqa: E402
from symbolic_ir.evaluation.citation import citation_scores  # noqa: E402
from symbolic_ir.evaluation.parser import parse_output  # noqa: E402


def generate_free_response(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = 64,
    patcher_context=None,
) -> str:
    """Generate free response using greedy decoding under optional causal intervention hook."""
    formatted = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )
    input_ids = tokenizer(formatted, return_tensors="pt")["input_ids"].to("cuda:0")

    ctx = patcher_context if patcher_context is not None else nullcontext()
    with ctx:
        with torch.inference_mode():
            output_ids = model.generate(
                input_ids=input_ids,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )

    gen_ids = output_ids[0, input_ids.shape[1] :]
    return tokenizer.decode(gen_ids, skip_special_tokens=True).strip()


class nullcontext:
    def __enter__(self):
        return None

    def __exit__(self, *args):
        return False


def score_behavioral_response(
    generated_text: str,
    expected_answer: str,
    gold_target_label: str,
    counterfactual_label: str,
    all_allowed_labels: list[str],
) -> dict[str, Any]:
    """Score free generation against expected answer, citation target, and error taxonomy."""
    parsed = parse_output(generated_text, allowed_ids=all_allowed_labels)
    ans_em = answer_exact_match(parsed.answer, expected_answer)
    cit_metrics = citation_scores(parsed.citations, (gold_target_label,))

    cites_gold = gold_target_label in parsed.citations
    cites_counterfactual = counterfactual_label in parsed.citations
    has_no_citation = len(parsed.citations) == 0
    cites_distractor = bool(set(parsed.citations) - {gold_target_label, counterfactual_label})
    spurious = len(parsed.invalid_ids) > 0 or len(parsed.malformed_ids) > 0

    # Error taxonomy
    error_type = "none"
    if not ans_em and not cites_gold:
        error_type = "both_incorrect"
    elif not ans_em:
        error_type = "answer_incorrect"
    elif cites_counterfactual:
        error_type = "counterfactual_cited"
    elif has_no_citation:
        error_type = "omitted_citation"
    elif cites_distractor:
        error_type = "wrong_source"
    elif spurious:
        error_type = "spurious_citation"

    # Selective dissociation: answer is preserved as expected, but citation shifted to counterfactual
    selective_dissociation = ans_em and cites_counterfactual

    return {
        "raw_text": generated_text,
        "parsed_answer": parsed.answer,
        "parsed_citations": list(parsed.citations),
        "answer_em": ans_em,
        "cites_gold": cites_gold,
        "cites_counterfactual": cites_counterfactual,
        "citation_precision": cit_metrics["citation_precision"],
        "citation_recall": cit_metrics["citation_recall"],
        "strict_syntax": parsed.strict_format,
        "has_citation_field": parsed.has_citation_field,
        "error_type": error_type,
        "selective_dissociation": selective_dissociation,
    }


def run_behavioral_bridge(
    config_path: Path,
    dataset_path: Path,
    output_path: Path,
    candidate_heads: list[int] | None = None,
    head_layer_1based: int = 24,
    basis_path: Path | None = None,
    subspace_layer_1based: int = 14,
    subspace_rank: int = 4,
    max_cases: int | None = None,
):
    """Run behavioral generation across clean, swapped, and causally patched prompts."""
    print("=" * 80)
    print("SEQUENCE 6: BEHAVIORAL BRIDGE & FREE GENERATION EVALUATION")
    print("=" * 80)
    print(f"Config:          {config_path}")
    print(f"Dataset:         {dataset_path}")
    print(f"Output:          {output_path}")
    print(f"Candidate Heads: {candidate_heads} at L{head_layer_1based}")
    print(f"Subspace:        {basis_path} (rank {subspace_rank}) at L{subspace_layer_1based}")

    cfg = load_config(resolve(config_path))
    model, tokenizer = load_model(cfg)
    model.eval()

    layers, _ = find_transformer_stack(model)

    # Setup head patching components if specified
    head_mod = None
    head_dim = None
    num_heads = None
    if candidate_heads:
        l_head_info = resolve_layer_indices(head_layer_1based, len(layers))
        head_mod = layers[l_head_info["layer_0based"]]
        num_heads = head_mod.self_attn.config.num_attention_heads
        hidden_size = head_mod.self_attn.config.hidden_size
        head_dim = getattr(head_mod.self_attn, "head_dim", hidden_size // num_heads)

    # Setup subspace components if specified
    subspace_mod = None
    subspace_basis = None
    if basis_path and basis_path.exists():
        l_sub_info = resolve_layer_indices(subspace_layer_1based, len(layers))
        subspace_mod = layers[l_sub_info["layer_0based"]]
        b_data = torch.load(basis_path, map_location="cpu", weights_only=False)
        subspace_basis = b_data["V"][:, :subspace_rank]

    lines = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if max_cases:
        lines = lines[:max_cases]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    results = []

    for idx, case in enumerate(lines):
        cid = case["example_id"]
        cond = case["condition"]
        clean_prompt = case["clean_prompt"]
        swapped_prompt = case["swapped_prompt"]
        expected_ans = case["answer"]
        clean_label = case["clean_label"]
        swapped_label = case["swapped_label"]
        rel_k = case["relevant_source_key"]

        all_allowed_labels = list(case["clean_display_by_source"].values())

        # 1. Clean Baseline Generation
        clean_text = generate_free_response(model, tokenizer, clean_prompt)
        clean_eval = score_behavioral_response(
            clean_text, expected_ans, clean_label, swapped_label, all_allowed_labels
        )

        # 2. Swapped Baseline Generation
        swapped_text = generate_free_response(model, tokenizer, swapped_prompt)
        swapped_eval = score_behavioral_response(
            swapped_text, expected_ans, swapped_label, clean_label, all_allowed_labels
        )

        case_rec = {
            "case_idx": idx,
            "example_id": cid,
            "condition": cond,
            "clean_baseline": clean_eval,
            "swapped_baseline": swapped_eval,
            "interventions": {},
        }

        # Locate semantic positions for interventions
        c_toks = tokenizer.encode(clean_label, add_special_tokens=False)
        s_toks = tokenizer.encode(swapped_label, add_special_tokens=False)
        dist_idx = find_first_distinguishing_index(c_toks, s_toks)

        rel_src = next(s for s in case["sources"] if s["key"] == rel_k)
        evidence_sentence = rel_src["text"].split(". ")[0] + "."
        clean_display = case["clean_display_by_source"][rel_k]
        swapped_display = case["swapped_display_by_source"][rel_k]

        clean_pos_dict = locate_semantic_positions(
            tokenizer=tokenizer,
            prompt=clean_prompt,
            answer=expected_ans,
            citation_label=clean_label,
            relevant_handle=clean_display,
            evidence_substring=evidence_sentence,
            dist_idx=dist_idx,
        )
        donor_pos_dict = locate_semantic_positions(
            tokenizer=tokenizer,
            prompt=swapped_prompt,
            answer=expected_ans,
            citation_label=swapped_label,
            relevant_handle=swapped_display,
            evidence_substring=evidence_sentence,
            dist_idx=dist_idx,
        )

        # 3. Head Intervention Generation (if candidate heads specified)
        if candidate_heads and head_mod:
            donor_cit_pos = donor_pos_dict["pos_citation"]
            clean_cit_pos = clean_pos_dict["pos_citation"]

            donor_input_ids = torch.tensor([donor_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")
            targets = [("donor_heads", head_mod.self_attn.o_proj, donor_cit_pos, num_heads, head_dim)]
            rec = MultiHeadActivationRecorder(targets)
            with torch.inference_mode():
                model(donor_input_ids)
            rec.close()
            donor_head_acts = rec.activations.get("donor_heads", {})
            del rec

            head_patcher = HeadSubsetPatcher(
                head_mod.self_attn.o_proj,
                heads_to_patch=candidate_heads,
                head_dim=head_dim,
                head_activations=donor_head_acts,
                target_positions=clean_cit_pos,
            )
            head_patched_text = generate_free_response(model, tokenizer, clean_prompt, patcher_context=head_patcher)
            head_eval = score_behavioral_response(
                head_patched_text, expected_ans, clean_label, swapped_label, all_allowed_labels
            )
            case_rec["interventions"]["candidate_heads"] = head_eval

        # 4. Subspace Intervention Generation (if subspace specified)
        if subspace_mod is not None and subspace_basis is not None:
            clean_pos = clean_pos_dict["pos_post_evidence"]
            donor_pos = donor_pos_dict["pos_post_evidence"]

            clean_input_ids = torch.tensor([clean_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")
            donor_input_ids = torch.tensor([donor_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")

            donor_act = None
            def cap_d(_m, _i, o):
                nonlocal donor_act
                primary = o[0] if isinstance(o, tuple) else o
                donor_act = primary[0, donor_pos, :].detach().cpu()
            h_d = subspace_mod.register_forward_hook(cap_d)
            with torch.inference_mode():
                model(donor_input_ids)
            h_d.remove()

            clean_act = None
            def cap_c(_m, _i, o):
                nonlocal clean_act
                primary = o[0] if isinstance(o, tuple) else o
                clean_act = primary[0, clean_pos, :].detach().cpu()
            h_c = subspace_mod.register_forward_hook(cap_c)
            with torch.inference_mode():
                model(clean_input_ids)
            h_c.remove()

            subspace_patcher = SubspaceProjectionPatcher(
                subspace_mod,
                subspace_basis,
                clean_act,
                donor_act,
                clean_pos,
            )
            sub_patched_text = generate_free_response(model, tokenizer, clean_prompt, patcher_context=subspace_patcher)
            sub_eval = score_behavioral_response(
                sub_patched_text, expected_ans, clean_label, swapped_label, all_allowed_labels
            )
            case_rec["interventions"]["subspace_projection"] = sub_eval

        torch.cuda.empty_cache()
        results.append(case_rec)
        with output_path.open("a", encoding="utf-8") as out_f:
            out_f.write(json.dumps(case_rec) + "\n")
            out_f.flush()

        if (idx + 1) % 5 == 0 or (idx + 1) == len(lines):
            print(f"[{idx+1}/{len(lines)}] Behavioral cases evaluated", flush=True)

    print(f"\nSaved {len(results)} behavioral generation records to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Sequence 6: Behavioral Bridge Evaluation")
    parser.add_argument("--config", default="configs/circuit/circuit_qwen25_15b.yaml")
    parser.add_argument("--dataset", default="data/circuit/validation_n32.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--candidate_heads", nargs="+", type=int, default=None)
    parser.add_argument("--head_layer", type=int, default=24)
    parser.add_argument("--basis_path", default=None)
    parser.add_argument("--subspace_layer", type=int, default=14)
    parser.add_argument("--subspace_rank", type=int, default=4)
    parser.add_argument("--max_cases", type=int, default=None)
    args = parser.parse_args()

    run_behavioral_bridge(
        config_path=Path(args.config),
        dataset_path=Path(args.dataset),
        output_path=Path(args.output),
        candidate_heads=args.candidate_heads,
        head_layer_1based=args.head_layer,
        basis_path=Path(args.basis_path) if args.basis_path else None,
        subspace_layer_1based=args.subspace_layer,
        subspace_rank=args.subspace_rank,
        max_cases=args.max_cases,
    )


if __name__ == "__main__":
    main()

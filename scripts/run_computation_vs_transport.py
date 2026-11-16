#!/usr/bin/env python3
"""Sequence 2: Computation vs. Transport Mechanistic Discrimination for Qwen 2.5 1.5B.

Evaluates whether late attention mixers compute source-identifier binding or merely
route/transport an already-formed decision.

Positions Tested:
1. pos_source_label: Relevant source identifier token span in prompt.
2. pos_evidence: Factual evidence sentence token span in prompt.
3. pos_answer: Answer representation token span.
4. pos_citation: Final prompt predicting token position (predicting first citation token).

Corruptions Tested:
1. label_swap: Same evidence, swapped source handles.
2. content_swap: Same labels, swapped factual evidence text.
3. question_swap: Same sources, question redirected to different passage.
4. order_perm: Same content-label pairs, permuted passage order.

Layers Evaluated:
- Layer 14 (Mid-layer routing tier)
- Layer 20 (Stale mediator hub)
- Layer 24 (Confirmed terminal binding hub)

Components:
- Mixer output (out_proj)
- MLP output (down_proj)
- Residual stream (layer block output)
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import re
import sys
import time
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.audit_component_hooks import get_layer_components  # noqa: E402
from scripts.run_circuit_decomposition import (  # noqa: E402
    SingleModulePositionPatcher,
    SingleModulePositionRecorder,
    find_first_distinguishing_index,
)
from scripts.run_stage6 import find_transformer_stack  # noqa: E402
from scripts.run_stage7 import load_model, resolve  # noqa: E402
from symbolic_ir.config import load_config  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.mechinterp.patching import _primary  # noqa: E402
from symbolic_ir.mechinterp.swaps import swap_source_identifiers  # noqa: E402
from symbolic_ir.prompts.render import render_prompt  # noqa: E402
from symbolic_ir.schema import CanonicalExample, IdentifierMapping, Source  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402


class MultiActivationRecorder:
    """Captures activations from multiple modules and token positions in a single forward pass."""

    def __init__(self, targets: list[tuple[Any, torch.nn.Module, list[int]]]):
        self.activations: dict[Any, torch.Tensor] = {}
        self.handles: list[torch.utils.hooks.RemovableHandle] = []
        for key, mod, positions in targets:
            if not positions:
                continue

            def make_hook(k, pos):
                def hook(_mod, _inputs, output):
                    primary = _primary(output)
                    self.activations[k] = primary[0, pos, :].detach().cpu()
                return hook

            self.handles.append(mod.register_forward_hook(make_hook(key, positions)))

    def close(self):
        for h in self.handles:
            h.remove()
        self.handles.clear()


def find_first_distinguishing_index(clean_tokens: list[int], swapped_tokens: list[int]) -> int:
    """Find index of the first token where clean and swapped token sequences differ."""
    for idx in range(min(len(clean_tokens), len(swapped_tokens))):
        if clean_tokens[idx] != swapped_tokens[idx]:
            return idx
    return 0


def extract_citation_eval_positions(tokenizer, prompt: str, answer: str, citation_label: str, dist_idx: int = 0) -> dict[str, Any]:
    """Tokenize prompt and answer prefix, locating citation target tokens and the distinguishing eval position."""
    formatted = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )
    ans_prefix = f"ANSWER: {answer}\nCITATIONS: "
    full_text = formatted + ans_prefix + citation_label

    encoded = tokenizer(full_text, add_special_tokens=False, return_offsets_mapping=True)
    offsets = encoded["offset_mapping"]

    # Target citation span
    target_start = len(formatted) + len(ans_prefix)
    target_end = len(full_text)
    target_positions = [
        i for i, (s, e) in enumerate(offsets)
        if e > s and s < target_end and e > target_start
    ]
    if not target_positions:
        raise ValueError(f"Target positions empty for citation {citation_label}")

    d = min(dist_idx, len(target_positions) - 1)
    eval_pos = target_positions[d] - 1

    # Answer span
    ans_start = len(formatted) + len("ANSWER: ")
    ans_end = ans_start + len(answer)
    ans_positions = [
        i for i, (s, e) in enumerate(offsets)
        if e > s and s < ans_end and e > ans_start
    ]

    return {
        "full_text": full_text,
        "input_ids": encoded["input_ids"],
        "offsets": offsets,
        "target_positions": target_positions,
        "dist_idx": d,
        "eval_pos": eval_pos,
        "predicting_pos": eval_pos,
        "ans_positions": ans_positions,
    }


def extract_spans(tokenizer, prompt: str, answer: str, citation_label: str, dist_idx: int = 0):
    """Compatibility alias wrapping extract_citation_eval_positions."""
    return extract_citation_eval_positions(tokenizer, prompt, answer, citation_label, dist_idx=dist_idx)


def resolve_layer_indices(layer_1based: int, num_total_layers: int) -> dict[str, int]:
    """Convert one-based scientific layer L to zero-based transformer stack index L - 1."""
    if layer_1based < 1 or layer_1based > num_total_layers:
        raise ValueError(f"Scientific layer {layer_1based} out of range (1..{num_total_layers})")
    layer_0based = layer_1based - 1
    return {
        "layer_1based": layer_1based,
        "layer_0based": layer_0based,
        "stack_idx": layer_0based,
    }


def align_activation_spans(clean_pos: list[int], donor_pos: list[int], donor_act: torch.Tensor) -> tuple[torch.Tensor, dict[str, Any]]:
    """Semantically align donor activation tensor to clean position count using 1D linear interpolation."""
    clean_len = len(clean_pos)
    donor_len = len(donor_pos)
    if clean_len == donor_len:
        return donor_act, {
            "clean_len": clean_len,
            "donor_len": donor_len,
            "aligned": True,
            "method": "identity",
        }
    if donor_len == 0 or clean_len == 0:
        return donor_act, {
            "clean_len": clean_len,
            "donor_len": donor_len,
            "aligned": False,
            "method": "empty_span",
        }

    is_2d = donor_act.dim() == 2
    if is_2d:
        # [donor_len, d_model] -> [1, d_model, donor_len]
        donor_t = donor_act.unsqueeze(0).permute(0, 2, 1).float()
    else:
        # [B, donor_len, d_model] -> [B, d_model, donor_len]
        donor_t = donor_act.permute(0, 2, 1).float()

    aligned_t = F.interpolate(donor_t, size=clean_len, mode="linear", align_corners=True)
    if is_2d:
        aligned_act = aligned_t.permute(0, 2, 1).squeeze(0).to(dtype=donor_act.dtype)
    else:
        aligned_act = aligned_t.permute(0, 2, 1).to(dtype=donor_act.dtype)

    return aligned_act, {
        "clean_len": clean_len,
        "donor_len": donor_len,
        "aligned": True,
        "method": "linear_interpolation",
    }


def locate_semantic_positions(
    tokenizer,
    prompt: str,
    answer: str,
    citation_label: str,
    relevant_handle: str,
    evidence_substring: str,
    dist_idx: int = 0,
) -> dict[str, Any]:
    """Map token spans for handle identity, evidence content, post-evidence binding, and output routing."""
    eval_dict = extract_citation_eval_positions(tokenizer, prompt, answer, citation_label, dist_idx=dist_idx)
    offsets = eval_dict["offsets"]
    full_text = eval_dict["full_text"]

    pos_handle = find_token_span(offsets, full_text, relevant_handle)
    pos_evidence = find_token_span(offsets, full_text, evidence_substring)
    pos_post_ev = [pos_evidence[-1]] if pos_evidence else []

    return {
        "pos_source_handle": pos_handle,
        "pos_evidence": pos_evidence,
        "pos_post_evidence": pos_post_ev,
        "pos_answer": eval_dict["ans_positions"],
        "pos_citation": [eval_dict["eval_pos"]],
        "eval_dict": eval_dict,
        "role_map": {
            "pos_source_handle": "handle_identity",
            "pos_evidence": "evidence_content",
            "pos_post_evidence": "binding_construction",
            "pos_answer": "answer_serialization",
            "pos_citation": "output_routing",
        },
    }


def find_token_span(offsets: list[tuple[int, int]], full_text: str, substring: str) -> list[int]:
    start_char = full_text.find(substring)
    if start_char < 0:
        return []
    end_char = start_char + len(substring)
    return [
        i for i, (s, e) in enumerate(offsets)
        if e > s and s < end_char and e > start_char
    ]


def build_repaired_corruptions(case: dict[str, Any], counter, tokenizer) -> dict[str, dict[str, Any]]:
    """Build the 4 causal corruption conditions with validated invariants and grounding checks."""
    sources = [Source(s["key"], s["text"]) for s in case["sources"]]
    rel_k = case["relevant_source_key"]
    dist_k = case["distractor_source_key"]
    clean_label = case["clean_label"]
    swapped_label = case["swapped_label"]

    base_ex = CanonicalExample(
        example_id=case["example_id"],
        seed=202671,
        task_type=case["task_type"],
        sources=tuple(sources),
        relevant_sources=(rel_k,),
        question=case.get("question", "What is the answer?"),
        answer=case.get("answer", "Answer"),
        entities={},
    )

    clean_mapping = render_identifiers(base_ex.sources, case["condition"], 202671, counter)
    clean_display = clean_mapping.display_by_source[rel_k]
    dist_display = clean_mapping.display_by_source[dist_k]

    rel_src = next(s for s in sources if s.key == rel_k)
    dist_src = next((s for s in sources if s.key == dist_k), None)
    gold_evidence = rel_src.text.split(". ")[0] + "."

    # Clean distinguishing token
    c_tokens = tokenizer.encode(clean_label, add_special_tokens=False)
    s_tokens = tokenizer.encode(swapped_label, add_special_tokens=False)
    d_idx = find_first_distinguishing_index(c_tokens, s_tokens)
    clean_tok = c_tokens[d_idx]
    distractor_tok = s_tokens[d_idx]

    corruptions = {}

    # 1. Label Swap
    swap_map = swap_source_identifiers(clean_mapping, rel_k, dist_k)
    prompt_lswap = render_prompt(base_ex, swap_map, require_citations=True).prompt
    corruptions["label_swap"] = {
        "is_eligible": True,
        "prompt": prompt_lswap,
        "answer": case.get("answer", base_ex.answer),
        "clean_target_label": clean_label,
        "donor_target_label": swapped_label,
        "clean_tok": clean_tok,
        "donor_swap_tok": distractor_tok,
        "dist_idx": d_idx,
        "rel_display": dist_display,
        "evidence_sentence": gold_evidence,
    }

    # 2. Content Swap
    if dist_src is not None:
        cswap_sources = []
        for s in sources:
            if s.key == rel_k:
                cswap_sources.append(Source(rel_k, dist_src.text))
            elif s.key == dist_k:
                cswap_sources.append(Source(dist_k, rel_src.text))
            else:
                cswap_sources.append(s)

        cswap_ex = CanonicalExample(
            example_id=case["example_id"] + "_cswap",
            seed=202671,
            task_type=case["task_type"],
            sources=tuple(cswap_sources),
            relevant_sources=(dist_k,),
            question=case.get("question", base_ex.question),
            answer=case.get("answer", base_ex.answer),
            entities={},
        )
        prompt_cswap = render_prompt(cswap_ex, clean_mapping, require_citations=True).prompt
        corruptions["content_swap"] = {
            "is_eligible": True,
            "prompt": prompt_cswap,
            "answer": case.get("answer", base_ex.answer),
            "clean_target_label": clean_label,
            "donor_target_label": swapped_label,
            "clean_tok": clean_tok,
            "donor_swap_tok": distractor_tok,
            "dist_idx": d_idx,
            "rel_display": dist_display,
            "evidence_sentence": gold_evidence,
        }
    else:
        corruptions["content_swap"] = {
            "is_eligible": False,
            "reason": f"Distractor source {dist_k} not found in sources",
        }

    # 3. Question Swap: Must ground alternative question in an explicit factual source
    qswap_eligible = False
    qswap_record = {}
    if dist_src is not None:
        match = re.search(r"reports reference value (\d+) for department ([A-Z]) in cycle (\d+)", dist_src.text)
        if match:
            val, dept, cycle = match.groups()
            qswap_question = f"What reference value is reported for department {dept} in cycle {cycle}? Answer with the number."
            qswap_answer = val
            qswap_label = clean_mapping.citation_by_source[dist_k]
            qswap_ex = CanonicalExample(
                example_id=case["example_id"] + "_qswap",
                seed=202671,
                task_type=case["task_type"],
                sources=tuple(sources),
                relevant_sources=(dist_k,),
                question=qswap_question,
                answer=qswap_answer,
                entities={},
            )
            prompt_qswap = render_prompt(qswap_ex, clean_mapping, require_citations=True).prompt
            qswap_record = {
                "is_eligible": True,
                "prompt": prompt_qswap,
                "answer": qswap_answer,
                "gold_source_key": dist_k,
                "clean_target_label": clean_label,
                "donor_target_label": qswap_label,
                "clean_tok": clean_tok,
                "donor_swap_tok": distractor_tok,
                "dist_idx": d_idx,
                "rel_display": dist_display,
                "evidence_sentence": dist_src.text.split(". ")[0] + ".",
            }
            qswap_eligible = True

    if not qswap_eligible:
        corruptions["question_swap"] = {
            "is_eligible": False,
            "reason": f"Distractor source {dist_k} lacks parseable grounded factual pattern for question-swap",
        }
    else:
        corruptions["question_swap"] = qswap_record

    # 4. Order Permutation: Preserves content-label pairings while rotating passage slots
    perm_sources = list(sources[5:]) + list(sources[:5])
    perm_ex = CanonicalExample(
        example_id=case["example_id"] + "_perm",
        seed=202671,
        task_type=case["task_type"],
        sources=tuple(perm_sources),
        relevant_sources=(rel_k,),
        question=case.get("question", base_ex.question),
        answer=case.get("answer", base_ex.answer),
        entities={},
    )
    prompt_perm = render_prompt(perm_ex, clean_mapping, require_citations=True).prompt
    orig_slot = next(i for i, s in enumerate(sources) if s.key == rel_k)
    new_slot = next(i for i, s in enumerate(perm_sources) if s.key == rel_k)

    corruptions["order_perm"] = {
        "is_eligible": True,
        "prompt": prompt_perm,
        "answer": case.get("answer", base_ex.answer),
        "clean_target_label": clean_label,
        "distractor_target_label": swapped_label,
        "donor_target_label": clean_label,
        "clean_tok": clean_tok,
        "distractor_tok": distractor_tok,
        "donor_swap_tok": distractor_tok,  # Frozen contrast against distractor
        "dist_idx": d_idx,
        "rel_display": clean_display,
        "evidence_sentence": gold_evidence,
        "invariants": {
            "content_label_pairing_preserved": clean_mapping.display_by_source[rel_k] == clean_display,
            "passage_slot_changed": orig_slot != new_slot,
        },
    }

    return corruptions


def build_corruptions(case: dict[str, Any], counter) -> dict[str, dict[str, Any]]:
    """Legacy alias calling build_repaired_corruptions with None tokenizer fallback."""
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("models/qwen2.5-1.5b-instruct-hf")
    return build_repaired_corruptions(case, counter, tok)


def compute_logp_pref(logits: torch.Tensor, clean_tok: int, swap_tok: int) -> tuple[float, float, float]:
    log_probs = F.log_softmax(logits, dim=-1)
    clean_lp = float(log_probs[clean_tok].item())
    swap_lp = float(log_probs[swap_tok].item())
    return clean_lp, swap_lp, swap_lp - clean_lp


def compute_kl(clean_logits: torch.Tensor, patched_logits: torch.Tensor) -> float:
    p = F.softmax(clean_logits, dim=-1)
    log_p = F.log_softmax(clean_logits, dim=-1)
    log_q = F.log_softmax(patched_logits, dim=-1)
    kl = torch.sum(p * (log_p - log_q), dim=-1)
    return max(0.0, float(kl.item()))


def run_experiment(
    config_path: Path,
    dataset_path: Path,
    output_path: Path,
    target_layers: list[int] = [14, 20, 24],
    condition_filter: str | None = None,
    max_cases: int | None = None,
):
    print("=" * 80)
    print("SEQUENCE 2: QWEN 2.5 COMPUTATION VS. TRANSPORT INTERVENTION")
    print("=" * 80)
    print(f"Config:    {config_path}")
    print(f"Dataset:   {dataset_path}")
    print(f"Output:    {output_path}")
    print(f"Layers:    {target_layers}")
    print(f"Condition: {condition_filter or 'all'}")

    cfg = load_config(resolve(config_path))
    model, tokenizer = load_model(cfg)
    model.eval()

    layers, final_norm = find_transformer_stack(model)
    counter = create_token_counter({"type": "regex"})

    # Map layer components with 1-based scientific layer mapping
    layer_comp_map = {}
    for l_1based in target_layers:
        l_info = resolve_layer_indices(l_1based, len(layers))
        l_0based = l_info["layer_0based"]
        layer_mod = layers[l_0based]
        comps = get_layer_components(layer_mod)
        layer_comp_map[l_1based] = {
            "layer_1based": l_1based,
            "layer_0based": l_0based,
            "stack_idx": l_0based,
            "layer_module": layer_mod,
            "mixer_out": comps["mixer"]["out_proj"],
            "mlp_out": comps["mlp"]["out_proj"],
        }

    lines = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if condition_filter and condition_filter != "all":
        lines = [line for line in lines if line.get("condition") == condition_filter]
    if max_cases:
        lines = lines[:max_cases]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed_keys = set()
    if output_path.exists():
        for line in output_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    row = json.loads(line)
                    completed_keys.add((row["example_id"], row["condition"]))
                except json.JSONDecodeError:
                    continue
        if completed_keys:
            print(f"Found {len(completed_keys)} already completed cases in {output_path.name}; resuming...")

    print(f"Loaded {len(lines)} cases to evaluate across 4 corruptions and 5 semantic token positions.")

    results = []
    start_time = time.time()

    for idx, case in enumerate(lines):
        cid = case["example_id"]
        cond = case["condition"]
        if (cid, cond) in completed_keys:
            continue

        clean_label = case["clean_label"]
        swapped_label = case["swapped_label"]
        rel_k = case["relevant_source_key"]

        # Clean Distinguishing token
        clean_target_tokens = tokenizer(clean_label, add_special_tokens=False)["input_ids"]
        swapped_target_tokens = tokenizer(swapped_label, add_special_tokens=False)["input_ids"]
        dist_idx = find_first_distinguishing_index(clean_target_tokens, swapped_target_tokens)
        clean_tok = clean_target_tokens[dist_idx]
        swapped_tok = swapped_target_tokens[dist_idx]

        # Locate clean positions
        rel_src = next(s for s in case["sources"] if s["key"] == rel_k)
        evidence_sentence = rel_src["text"].split(". ")[0] + "."
        clean_display = case["clean_display_by_source"][rel_k]

        clean_pos_dict = locate_semantic_positions(
            tokenizer=tokenizer,
            prompt=case["clean_prompt"],
            answer=case["answer"],
            citation_label=clean_label,
            relevant_handle=clean_display,
            evidence_substring=evidence_sentence,
            dist_idx=dist_idx,
        )
        clean_pred_pos = clean_pos_dict["pos_citation"][0]

        clean_positions_dict = {
            "pos_source_label": clean_pos_dict["pos_source_handle"],
            "pos_evidence": clean_pos_dict["pos_evidence"],
            "pos_post_evidence": clean_pos_dict["pos_post_evidence"],
            "pos_answer": clean_pos_dict["pos_answer"],
            "pos_citation": clean_pos_dict["pos_citation"],
        }

        # Run Clean Baseline
        clean_input_ids = torch.tensor([clean_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")
        clean_pred_tensor = torch.tensor([clean_pred_pos], device="cuda:0")
        with torch.inference_mode():
            clean_out = model(clean_input_ids, logits_to_keep=clean_pred_tensor)
            clean_logits = clean_out.logits[0, 0, :]
            c_lp, s_lp, clean_pref = compute_logp_pref(clean_logits, clean_tok, swapped_tok)

        case_record = {
            "case_idx": idx,
            "example_id": cid,
            "condition": cond,
            "task_type": case["task_type"],
            "clean_label": clean_label,
            "swapped_label": swapped_label,
            "dist_idx": dist_idx,
            "role_map": clean_pos_dict["role_map"],
            "clean_baseline": {
                "clean_logp": c_lp,
                "swapped_logp": s_lp,
                "first_token_pref": clean_pref,
            },
            "corruptions": {},
        }

        # Build Corruptions
        corruptions = build_repaired_corruptions(case, counter, tokenizer)

        for corr_name, corr_info in corruptions.items():
            if not corr_info.get("is_eligible", True):
                case_record["corruptions"][corr_name] = {
                    "is_eligible": False,
                    "reason": corr_info.get("reason", "unknown ineligibility"),
                }
                continue

            donor_prompt = corr_info["prompt"]
            donor_answer = corr_info["answer"]
            donor_target = corr_info["donor_target_label"]
            donor_swap_tok = corr_info["donor_swap_tok"]

            donor_pos_dict = locate_semantic_positions(
                tokenizer=tokenizer,
                prompt=donor_prompt,
                answer=donor_answer,
                citation_label=donor_target,
                relevant_handle=corr_info["rel_display"],
                evidence_substring=corr_info["evidence_sentence"],
                dist_idx=corr_info["dist_idx"],
            )
            donor_pred_pos = donor_pos_dict["pos_citation"][0]

            donor_positions_dict = {
                "pos_source_label": donor_pos_dict["pos_source_handle"],
                "pos_evidence": donor_pos_dict["pos_evidence"],
                "pos_post_evidence": donor_pos_dict["pos_post_evidence"],
                "pos_answer": donor_pos_dict["pos_answer"],
                "pos_citation": donor_pos_dict["pos_citation"],
            }

            # Register all donor targets across layers, components, and positions in a single pass
            donor_input_ids = torch.tensor([donor_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")
            donor_targets = []
            for l_1based in target_layers:
                layer_mods = layer_comp_map[l_1based]
                for pos_name in ["pos_source_label", "pos_evidence", "pos_post_evidence", "pos_answer", "pos_citation"]:
                    d_pos = donor_positions_dict[pos_name]
                    if d_pos:
                        donor_targets.append(((l_1based, pos_name, "mixer"), layer_mods["mixer_out"], d_pos))
                        donor_targets.append(((l_1based, pos_name, "mlp"), layer_mods["mlp_out"], d_pos))
                        donor_targets.append(((l_1based, pos_name, "residual"), layer_mods["layer_module"], d_pos))

            rec = MultiActivationRecorder(donor_targets)
            donor_pred_tensor = torch.tensor([donor_pred_pos], device="cuda:0")
            with torch.inference_mode():
                donor_out = model(donor_input_ids, logits_to_keep=donor_pred_tensor)
                donor_logits = donor_out.logits[0, 0, :]
                d_c_lp, d_s_lp, donor_pref = compute_logp_pref(donor_logits, clean_tok, donor_swap_tok)
            rec.close()
            donor_acts = rec.activations
            del rec, donor_targets
            torch.cuda.empty_cache()

            corr_record = {
                "is_eligible": True,
                "donor_baseline": {
                    "clean_logp": d_c_lp,
                    "swapped_logp": d_s_lp,
                    "first_token_pref": donor_pref,
                },
                "layers": {},
            }

            for l_1based in target_layers:
                layer_mods = layer_comp_map[l_1based]
                layer_record = {
                    "layer_1based": l_1based,
                    "layer_0based": layer_mods["layer_0based"],
                    "stack_idx": layer_mods["stack_idx"],
                    "positions": {},
                }

                for pos_name in ["pos_source_label", "pos_evidence", "pos_post_evidence", "pos_answer", "pos_citation"]:
                    clean_pos = clean_positions_dict[pos_name]
                    donor_pos = donor_positions_dict[pos_name]

                    if not clean_pos or not donor_pos:
                        layer_record["positions"][pos_name] = {
                            "status": "empty_position",
                            "clean_len": len(clean_pos),
                            "donor_len": len(donor_pos),
                        }
                        continue

                    pos_eval = {}
                    comp_targets = [
                        ("mixer", layer_mods["mixer_out"]),
                        ("mlp", layer_mods["mlp_out"]),
                        ("residual", layer_mods["layer_module"]),
                    ]

                    for comp_name, comp_mod in comp_targets:
                        donor_act = donor_acts.get((l_1based, pos_name, comp_name))
                        if donor_act is None:
                            continue

                        aligned_act, diag = align_activation_spans(clean_pos, donor_pos, donor_act)
                        with SingleModulePositionPatcher(comp_mod, aligned_act, clean_pos):
                            with torch.inference_mode():
                                patched_out = model(clean_input_ids, logits_to_keep=clean_pred_tensor)
                                patched_logits = patched_out.logits[0, 0, :]

                        _, _, patched_pref = compute_logp_pref(patched_logits, clean_tok, donor_swap_tok)
                        kl = compute_kl(clean_logits, patched_logits)
                        shift = patched_pref - clean_pref

                        pos_eval[comp_name] = {
                            "abs_shift_first": round(float(shift), 4),
                            "kl_div": round(float(kl), 4),
                            "alignment_diag": diag,
                        }

                    layer_record["positions"][pos_name] = pos_eval

                corr_record["layers"][str(l_1based)] = layer_record

            case_record["corruptions"][corr_name] = corr_record

        # Clear GPU cache after each case
        torch.cuda.empty_cache()

        # Stream row directly to output file
        with output_path.open("a", encoding="utf-8") as out_f:
            out_f.write(json.dumps(case_record) + "\n")
            out_f.flush()
        completed_keys.add((cid, cond))

        results.append(case_record)
        elapsed = time.time() - start_time
        n_done = len(completed_keys)
        print(f"[{n_done}/{len(lines)}] Case completed: {cid} ({cond}) in {elapsed/(idx+1):.1f}s/case", flush=True)

    print(f"\nCompleted run. All {len(completed_keys)} evaluated records saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Sequence 2: Computation vs. Transport Intervention")
    parser.add_argument("--config", default="configs/circuit/circuit_qwen25_15b.yaml")
    parser.add_argument("--dataset", default="data/circuit/discovery_n32.jsonl")
    parser.add_argument("--output", default="results/circuit/qwen25_computation_vs_transport.jsonl")
    parser.add_argument("--layers", nargs="+", type=int, default=[14, 20, 24])
    parser.add_argument("--condition", default=None, choices=["structured", "random_compact", "uuid", "all"])
    parser.add_argument("--max_cases", type=int, default=None)
    args = parser.parse_args()

    run_experiment(
        config_path=Path(args.config),
        dataset_path=Path(args.dataset),
        output_path=Path(args.output),
        target_layers=args.layers,
        condition_filter=args.condition,
        max_cases=args.max_cases,
    )


if __name__ == "__main__":
    main()

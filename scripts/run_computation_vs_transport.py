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


def extract_spans(tokenizer, prompt: str, answer: str, citation_label: str):
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

    predicting_pos = target_positions[0] - 1

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
        "predicting_pos": predicting_pos,
        "target_positions": target_positions,
        "ans_positions": ans_positions,
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


def build_corruptions(case: dict[str, Any], counter) -> dict[str, dict[str, Any]]:
    """Build the 4 corruption conditions from a base case."""
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
        question=case["question"],
        answer=case["answer"],
        entities={},
    )

    clean_mapping = render_identifiers(base_ex.sources, case["condition"], 202671, counter)
    clean_display = clean_mapping.display_by_source[rel_k]
    dist_display = clean_mapping.display_by_source[dist_k]

    # Gold evidence sentence is the first sentence of the relevant source
    rel_src = next(s for s in sources if s.key == rel_k)
    dist_src = next(s for s in sources if s.key == dist_k)
    gold_evidence = rel_src.text.split(". ")[0] + "."

    corruptions = {}

    # 1. Label Swap: Swapped handles between rel_k and dist_k
    swap_map = swap_source_identifiers(clean_mapping, rel_k, dist_k)
    prompt_lswap = render_prompt(base_ex, swap_map, require_citations=True).prompt
    corruptions["label_swap"] = {
        "prompt": prompt_lswap,
        "answer": case["answer"],
        "donor_target_label": swapped_label,
        "rel_display": dist_display,  # At rel_k, label is now dist_display
        "evidence_sentence": gold_evidence,
    }

    # 2. Content Swap: Swap factual text between rel_k and dist_k
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
        question=case["question"],
        answer=case["answer"],
        entities={},
    )
    prompt_cswap = render_prompt(cswap_ex, clean_mapping, require_citations=True).prompt
    corruptions["content_swap"] = {
        "prompt": prompt_cswap,
        "answer": case["answer"],
        "donor_target_label": swapped_label,
        "rel_display": dist_display,  # Gold fact is now in dist_k with label dist_display
        "evidence_sentence": gold_evidence,
    }

    # 3. Question Swap: Question asks about another source
    # For temporal: "review" fact is present in sources
    review_src = next((s for s in sources if "review" in s.key or s.key != rel_k and s.key != dist_k), dist_src)
    qswap_question = "Which source reports the design review?" if case["task_type"] == "temporal" else "Which source reports the secondary registry record?"
    qswap_answer = "design review" if case["task_type"] == "temporal" else "registry record"
    qswap_label = clean_mapping.citation_by_source[review_src.key]

    qswap_ex = CanonicalExample(
        example_id=case["example_id"] + "_qswap",
        seed=202671,
        task_type=case["task_type"],
        sources=tuple(sources),
        relevant_sources=(review_src.key,),
        question=qswap_question,
        answer=qswap_answer,
        entities={},
    )
    prompt_qswap = render_prompt(qswap_ex, clean_mapping, require_citations=True).prompt
    corruptions["question_swap"] = {
        "prompt": prompt_qswap,
        "answer": qswap_answer,
        "donor_target_label": qswap_label,
        "rel_display": clean_mapping.display_by_source[review_src.key],
        "evidence_sentence": review_src.text.split(". ")[0] + ".",
    }

    # 4. Order Permutation: Rotate passages by 5 slots (content-label pairs preserved)
    perm_sources = list(sources[5:]) + list(sources[:5])
    perm_ex = CanonicalExample(
        example_id=case["example_id"] + "_perm",
        seed=202671,
        task_type=case["task_type"],
        sources=tuple(perm_sources),
        relevant_sources=(rel_k,),
        question=case["question"],
        answer=case["answer"],
        entities={},
    )
    prompt_perm = render_prompt(perm_ex, clean_mapping, require_citations=True).prompt
    corruptions["order_perm"] = {
        "prompt": prompt_perm,
        "answer": case["answer"],
        "donor_target_label": clean_label,  # Same label expected!
        "rel_display": clean_display,
        "evidence_sentence": gold_evidence,
    }

    return corruptions


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

    # Map layer components
    layer_comp_map = {}
    for l_idx in target_layers:
        layer_mod = layers[l_idx]
        comps = get_layer_components(layer_mod)
        layer_comp_map[l_idx] = {
            "layer_module": layer_mod,
            "mixer_out": comps["mixer"]["out_proj"],
            "mlp_out": comps["mlp"]["out_proj"],
        }

    lines = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if condition_filter and condition_filter != "all":
        lines = [line for line in lines if line.get("condition") == condition_filter]
    if max_cases:
        lines = lines[:max_cases]
    print(f"Loaded {len(lines)} cases to evaluate across 4 corruptions and 4 token positions.")

    results = []
    start_time = time.time()

    for idx, case in enumerate(lines):
        cid = case["example_id"]
        cond = case["condition"]
        clean_label = case["clean_label"]
        swapped_label = case["swapped_label"]
        rel_k = case["relevant_source_key"]

        # Parse Clean Spans
        clean_spans = extract_spans(tokenizer, case["clean_prompt"], case["answer"], clean_label)
        clean_full_text = clean_spans["full_text"]
        clean_offsets = clean_spans["offsets"]
        clean_pred_pos = clean_spans["predicting_pos"]

        # Tokenize distinguishing first token
        clean_target_tokens = tokenizer(clean_label, add_special_tokens=False)["input_ids"]
        swapped_target_tokens = tokenizer(swapped_label, add_special_tokens=False)["input_ids"]
        dist_idx = find_first_distinguishing_index(clean_target_tokens, swapped_target_tokens)
        clean_tok = clean_target_tokens[dist_idx]
        swapped_tok = swapped_target_tokens[dist_idx]

        # Locate clean positions
        rel_src = next(s for s in case["sources"] if s["key"] == rel_k)
        evidence_sentence = rel_src["text"].split(". ")[0] + "."
        clean_display = case["clean_display_by_source"][rel_k]

        pos_label_clean = find_token_span(clean_offsets, clean_full_text, clean_display)
        pos_evidence_clean = find_token_span(clean_offsets, clean_full_text, evidence_sentence)
        pos_answer_clean = clean_spans["ans_positions"]
        pos_citation_clean = [clean_pred_pos]

        clean_positions_dict = {
            "pos_source_label": pos_label_clean,
            "pos_evidence": pos_evidence_clean,
            "pos_answer": pos_answer_clean,
            "pos_citation": pos_citation_clean,
        }

        # Run Clean Baseline
        clean_input_ids = torch.tensor([clean_spans["input_ids"]], device="cuda:0")
        with torch.no_grad():
            clean_out = model(clean_input_ids)
            clean_logits = clean_out.logits[0, clean_pred_pos, :]
            c_lp, s_lp, clean_pref = compute_logp_pref(clean_logits, clean_tok, swapped_tok)

        case_record = {
            "case_idx": idx,
            "example_id": cid,
            "condition": cond,
            "task_type": case["task_type"],
            "clean_label": clean_label,
            "swapped_label": swapped_label,
            "clean_baseline": {
                "clean_logp": c_lp,
                "swapped_logp": s_lp,
                "first_token_pref": clean_pref,
            },
            "corruptions": {},
        }

        # Build Corruptions
        corruptions = build_corruptions(case, counter)

        for corr_name, corr_info in corruptions.items():
            donor_prompt = corr_info["prompt"]
            donor_answer = corr_info["answer"]
            donor_target = corr_info["donor_target_label"]

            donor_spans = extract_spans(tokenizer, donor_prompt, donor_answer, donor_target)
            donor_full_text = donor_spans["full_text"]
            donor_offsets = donor_spans["offsets"]
            donor_pred_pos = donor_spans["predicting_pos"]

            donor_target_toks = tokenizer(donor_target, add_special_tokens=False)["input_ids"]
            donor_dist_idx = find_first_distinguishing_index(clean_target_tokens, donor_target_toks)
            donor_swap_tok = donor_target_toks[donor_dist_idx] if donor_dist_idx < len(donor_target_toks) else swapped_tok

            # Locate donor positions
            pos_label_donor = find_token_span(donor_offsets, donor_full_text, corr_info["rel_display"])
            pos_evidence_donor = find_token_span(donor_offsets, donor_full_text, corr_info["evidence_sentence"])
            pos_answer_donor = donor_spans["ans_positions"]
            pos_citation_donor = [donor_pred_pos]

            donor_positions_dict = {
                "pos_source_label": pos_label_donor,
                "pos_evidence": pos_evidence_donor,
                "pos_answer": pos_answer_donor,
                "pos_citation": pos_citation_donor,
            }

            # Register all donor targets across layers, components, and positions in a single pass
            donor_input_ids = torch.tensor([donor_spans["input_ids"]], device="cuda:0")
            donor_targets = []
            for l_idx in target_layers:
                layer_mods = layer_comp_map[l_idx]
                for pos_name in ["pos_source_label", "pos_evidence", "pos_answer", "pos_citation"]:
                    d_pos = donor_positions_dict[pos_name]
                    if d_pos:
                        donor_targets.append(((l_idx, pos_name, "mixer"), layer_mods["mixer_out"], d_pos))
                        donor_targets.append(((l_idx, pos_name, "mlp"), layer_mods["mlp_out"], d_pos))
                        donor_targets.append(((l_idx, pos_name, "residual"), layer_mods["layer_module"], d_pos))

            rec = MultiActivationRecorder(donor_targets)
            with torch.no_grad():
                donor_out = model(donor_input_ids)
                donor_logits = donor_out.logits[0, donor_pred_pos, :]
                d_c_lp, d_s_lp, donor_pref = compute_logp_pref(donor_logits, clean_tok, donor_swap_tok)
            rec.close()
            donor_acts = rec.activations
            del rec, donor_targets
            torch.cuda.empty_cache()

            corr_record = {
                "donor_baseline": {
                    "clean_logp": d_c_lp,
                    "swapped_logp": d_s_lp,
                    "first_token_pref": donor_pref,
                },
                "layers": {},
            }

            for l_idx in target_layers:
                layer_mods = layer_comp_map[l_idx]
                layer_record = {}

                for pos_name in ["pos_source_label", "pos_evidence", "pos_answer", "pos_citation"]:
                    clean_pos = clean_positions_dict[pos_name]
                    donor_pos = donor_positions_dict[pos_name]

                    # Token length alignment check
                    if not clean_pos or not donor_pos or len(clean_pos) != len(donor_pos):
                        layer_record[pos_name] = {"status": "length_mismatch", "clean_len": len(clean_pos), "donor_len": len(donor_pos)}
                        continue

                    pos_eval = {}
                    comp_targets = [
                        ("mixer", layer_mods["mixer_out"]),
                        ("mlp", layer_mods["mlp_out"]),
                        ("residual", layer_mods["layer_module"]),
                    ]

                    for comp_name, comp_mod in comp_targets:
                        donor_act = donor_acts.get((l_idx, pos_name, comp_name))
                        if donor_act is None:
                            continue

                        with SingleModulePositionPatcher(comp_mod, donor_act, clean_pos):
                            with torch.no_grad():
                                patched_out = model(clean_input_ids)
                                patched_logits = patched_out.logits[0, clean_pred_pos, :]

                        _, _, patched_pref = compute_logp_pref(patched_logits, clean_tok, donor_swap_tok)
                        kl = compute_kl(clean_logits, patched_logits)
                        shift = patched_pref - clean_pref

                        pos_eval[comp_name] = {
                            "abs_shift_first": round(float(shift), 4),
                            "kl_div": round(float(kl), 4),
                        }

                    layer_record[pos_name] = pos_eval

                corr_record["layers"][str(l_idx)] = layer_record

            case_record["corruptions"][corr_name] = corr_record

        # Clear GPU cache after each case
        torch.cuda.empty_cache()

        results.append(case_record)
        if (idx + 1) % 10 == 0 or (idx + 1) == len(lines):
            elapsed = time.time() - start_time
            print(f"[{idx+1}/{len(lines)}] Cases evaluated ({elapsed:.1f}s, {elapsed/(idx+1):.2f}s/case)")

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nSaved {len(results)} evaluated records to {output_path}")


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

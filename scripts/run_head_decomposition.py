#!/usr/bin/env python3
"""Phase 4: Head-Level Circuit Decomposition Runner for Qwen 2.5 1.5B.

Isolates individual query attention heads and candidate head subsets within
identified causal mixer layers to evaluate:
1. Individual head attribution and ranking (Discovery).
2. Candidate subset sufficiency and random-subset controls (Validation).
3. Candidate subset necessity via matched-mean and zero ablation.
4. Exact minimality across 2^K subsets for K <= 4.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
import time
from contextlib import AbstractContextManager, nullcontext
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
from scripts.run_computation_vs_transport import (  # noqa: E402
    compute_kl,
    compute_logp_pref,
    extract_citation_eval_positions,
    find_first_distinguishing_index,
    locate_semantic_positions,
    resolve_layer_indices,
)
from scripts.run_stage6 import find_transformer_stack  # noqa: E402
from scripts.run_stage7 import load_model, resolve  # noqa: E402
from symbolic_ir.config import load_config  # noqa: E402


class MultiHeadActivationRecorder:
    """Captures unprojected query-head activations at o_proj forward pre-hook in a single forward pass."""

    def __init__(self, targets: list[tuple[Any, torch.nn.Module, list[int], int, int]]):
        # targets: list of (key, o_proj_module, positions, num_heads, head_dim)
        self.activations: dict[Any, dict[int, torch.Tensor]] = {}
        self.handles: list[torch.utils.hooks.RemovableHandle] = []

        for key, o_proj_mod, positions, num_heads, head_dim in targets:
            if not positions:
                continue

            def make_hook(k, pos, n_h, h_dim):
                def hook(_mod, inputs):
                    tensor = inputs[0]  # [B, S, hidden_size]
                    head_map = {}
                    for h in range(n_h):
                        start_col = h * h_dim
                        end_col = (h + 1) * h_dim
                        head_map[h] = tensor[0, pos, start_col:end_col].detach().cpu()
                    self.activations[k] = head_map
                return hook

            self.handles.append(o_proj_mod.register_forward_pre_hook(make_hook(key, positions, num_heads, head_dim)))

    def close(self):
        for h in self.handles:
            h.remove()
        self.handles.clear()


class HeadSubsetPatcher(AbstractContextManager):
    """Patches a specific subset of query heads at target positions during o_proj forward pass."""

    def __init__(
        self,
        o_proj_module: torch.nn.Module,
        heads_to_patch: list[int] | set[int],
        head_dim: int,
        head_activations: dict[int, torch.Tensor],
        target_positions: list[int],
    ):
        self.o_proj_module = o_proj_module
        self.heads_to_patch = set(heads_to_patch)
        self.head_dim = head_dim
        self.head_activations = head_activations
        self.target_positions = target_positions
        self.handle = None

    def __enter__(self):
        def patch(_module, inputs):
            tensor = inputs[0]
            if not self.target_positions or max(self.target_positions) >= tensor.shape[1]:
                return inputs
            modified = tensor.clone()
            for h in self.heads_to_patch:
                start_col = h * self.head_dim
                end_col = (h + 1) * self.head_dim
                donor_act = self.head_activations[h].to(device=modified.device, dtype=modified.dtype)
                if donor_act.dim() == 2:
                    donor_act = donor_act.unsqueeze(0)
                modified[:, self.target_positions, start_col:end_col] = donor_act.expand(modified.shape[0], -1, -1)
            return (modified,)

        self.handle = self.o_proj_module.register_forward_pre_hook(patch)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handle is not None:
            self.handle.remove()
            self.handle = None
        return False


class HeadAblationPatcher(AbstractContextManager):
    """Ablates a specific subset of query heads using either zero ablation or precomputed dataset mean."""

    def __init__(
        self,
        o_proj_module: torch.nn.Module,
        heads_to_ablate: list[int] | set[int],
        head_dim: int,
        target_positions: list[int],
        mode: str = "zero",  # 'zero' or 'mean'
        mean_activations: dict[int, torch.Tensor] | None = None,
    ):
        self.o_proj_module = o_proj_module
        self.heads_to_ablate = set(heads_to_ablate)
        self.head_dim = head_dim
        self.target_positions = target_positions
        self.mode = mode
        self.mean_activations = mean_activations or {}
        self.handle = None

    def __enter__(self):
        def ablate(_module, inputs):
            tensor = inputs[0]
            if not self.target_positions or max(self.target_positions) >= tensor.shape[1]:
                return inputs
            modified = tensor.clone()
            for h in self.heads_to_ablate:
                start_col = h * self.head_dim
                end_col = (h + 1) * self.head_dim
                if self.mode == "mean" and h in self.mean_activations:
                    vals = self.mean_activations[h].to(device=modified.device, dtype=modified.dtype)
                    if vals.dim() == 2:
                        vals = vals.unsqueeze(0)
                    modified[:, self.target_positions, start_col:end_col] = vals.expand(modified.shape[0], -1, -1)
                else:
                    modified[:, self.target_positions, start_col:end_col] = 0.0
            return (modified,)

        self.handle = self.o_proj_module.register_forward_pre_hook(ablate)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handle is not None:
            self.handle.remove()
            self.handle = None
        return False


def run_head_screening(
    config_path: Path,
    dataset_path: Path,
    output_path: Path,
    target_layer_1based: int = 24,
    semantic_position_key: str = "pos_citation",
    max_cases: int | None = None,
):
    """Run individual head causal screening across all query heads on the discovery cohort."""
    print("=" * 80)
    print("SEQUENCE 3A: QUERY ATTENTION HEAD CAUSAL SCREENING")
    print("=" * 80)
    print(f"Config:          {config_path}")
    print(f"Dataset:         {dataset_path}")
    print(f"Output:          {output_path}")
    print(f"Target Layer:    L{target_layer_1based}")
    print(f"Semantic Pos:    {semantic_position_key}")

    cfg = load_config(resolve(config_path))
    model, tokenizer = load_model(cfg)
    model.eval()

    layers, _ = find_transformer_stack(model)
    layer_info = resolve_layer_indices(target_layer_1based, len(layers))
    target_mod = layers[layer_info["layer_0based"]]

    # Assert model architecture parameters
    assert hasattr(target_mod, "self_attn"), "Target layer missing self_attn"
    assert hasattr(target_mod.self_attn, "o_proj"), "Target self_attn missing o_proj"

    num_heads = target_mod.self_attn.config.num_attention_heads
    hidden_size = target_mod.self_attn.config.hidden_size
    head_dim = getattr(target_mod.self_attn, "head_dim", hidden_size // num_heads)

    print(f"Layer L{target_layer_1based} (stack {layer_info['layer_0based']}): {num_heads} query heads, head_dim={head_dim}")

    lines = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
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
            print(f"Resuming: {len(completed_keys)} cases already completed in {output_path.name}")

    print(f"Loaded {len(lines)} cases to evaluate across {num_heads} query heads.")
    start_time = time.time()

    for idx, case in enumerate(lines):
        cid = case["example_id"]
        cond = case["condition"]
        if (cid, cond) in completed_keys:
            continue

        clean_label = case["clean_label"]
        swapped_label = case["swapped_label"]
        rel_k = case["relevant_source_key"]

        # Clean Distinguishing Token
        c_toks = tokenizer.encode(clean_label, add_special_tokens=False)
        s_toks = tokenizer.encode(swapped_label, add_special_tokens=False)
        dist_idx = find_first_distinguishing_index(c_toks, s_toks)
        clean_tok = c_toks[dist_idx]
        swapped_tok = s_toks[dist_idx]

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
        clean_target_pos = clean_pos_dict[semantic_position_key]
        clean_pred_pos = clean_pos_dict["pos_citation"][0]

        # Clean Baseline
        clean_input_ids = torch.tensor([clean_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")
        with torch.inference_mode():
            clean_out = model(clean_input_ids)
            clean_logits = clean_out.logits[0, clean_pred_pos, :]
            c_lp, s_lp, clean_pref = compute_logp_pref(clean_logits, clean_tok, swapped_tok)

        # Donor run (swapped prompt)
        swapped_display = case["swapped_display_by_source"][rel_k]
        donor_pos_dict = locate_semantic_positions(
            tokenizer=tokenizer,
            prompt=case["swapped_prompt"],
            answer=case["answer"],
            citation_label=swapped_label,
            relevant_handle=swapped_display,
            evidence_substring=evidence_sentence,
            dist_idx=dist_idx,
        )
        donor_target_pos = donor_pos_dict[semantic_position_key]
        donor_pred_pos = donor_pos_dict["pos_citation"][0]
        donor_input_ids = torch.tensor([donor_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")

        # Single-pass capture of all heads on donor
        targets = [("donor_heads", target_mod.self_attn.o_proj, donor_target_pos, num_heads, head_dim)]
        rec = MultiHeadActivationRecorder(targets)
        with torch.inference_mode():
            donor_out = model(donor_input_ids)
            donor_logits = donor_out.logits[0, donor_pred_pos, :]
            d_c_lp, d_s_lp, donor_pref = compute_logp_pref(donor_logits, clean_tok, swapped_tok)
        rec.close()
        donor_head_acts = rec.activations.get("donor_heads", {})
        del rec, targets
        torch.cuda.empty_cache()

        case_record = {
            "case_idx": idx,
            "example_id": cid,
            "condition": cond,
            "layer_1based": target_layer_1based,
            "layer_0based": layer_info["layer_0based"],
            "stack_idx": layer_info["stack_idx"],
            "semantic_position": semantic_position_key,
            "clean_baseline": {
                "clean_logp": c_lp,
                "swapped_logp": s_lp,
                "first_token_pref": clean_pref,
            },
            "donor_baseline": {
                "clean_logp": d_c_lp,
                "swapped_logp": d_s_lp,
                "first_token_pref": donor_pref,
            },
            "head_results": {},
        }

        denom = donor_pref - clean_pref

        # Test each head individually
        for h in range(num_heads):
            patcher = HeadSubsetPatcher(
                target_mod.self_attn.o_proj,
                heads_to_patch=[h],
                head_dim=head_dim,
                head_activations=donor_head_acts,
                target_positions=clean_target_pos,
            )
            with patcher:
                with torch.inference_mode():
                    patched_out = model(clean_input_ids)
                    patched_logits = patched_out.logits[0, clean_pred_pos, :]

            _, _, patched_pref = compute_logp_pref(patched_logits, clean_tok, swapped_tok)
            shift = patched_pref - clean_pref
            kl = compute_kl(clean_logits, patched_logits)
            recov = (shift / denom * 100.0) if abs(denom) > 0.5 else None

            case_record["head_results"][str(h)] = {
                "head": h,
                "abs_shift_first": round(float(shift), 4),
                "recovery_pct": round(float(recov), 2) if recov is not None else None,
                "kl_div": round(float(kl), 4),
            }

        # Clear GPU cache after each case
        torch.cuda.empty_cache()

        # Stream row directly to output file
        with output_path.open("a", encoding="utf-8") as out_f:
            out_f.write(json.dumps(case_record) + "\n")
            out_f.flush()
        completed_keys.add((cid, cond))

        elapsed = time.time() - start_time
        n_done = len(completed_keys)
        print(f"[{n_done}/{len(lines)}] Case evaluated: {cid} ({cond}) in {elapsed/(idx+1):.1f}s/case", flush=True)

    print(f"\nAll {len(completed_keys)} head screening records saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Sequence 3A: Head-Level Decomposition")
    parser.add_argument("--config", default="configs/circuit/circuit_qwen25_15b.yaml")
    parser.add_argument("--dataset", default="data/circuit/discovery_n32.jsonl")
    parser.add_argument("--output", default="results/circuit/sequence3_work/qwen25_head_scores_discovery_l24.jsonl")
    parser.add_argument("--layer", type=int, default=24)
    parser.add_argument("--pos", default="pos_citation")
    parser.add_argument("--max_cases", type=int, default=None)
    args = parser.parse_args()

    run_head_screening(
        config_path=Path(args.config),
        dataset_path=Path(args.dataset),
        output_path=Path(args.output),
        target_layer_1based=args.layer,
        semantic_position_key=args.pos,
        max_cases=args.max_cases,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Phase 2 & 3: Component-Level Circuit Decomposition (Attention/Mixer vs MLP).

For each layer in the candidate window:
1. Intercepts mixer output (self_attn.o_proj or linear_attn.out_proj) alone.
2. Intercepts MLP output (mlp.down_proj) alone.
3. Intercepts joint layer output (positive control).

Measures behavioral outcome dissociation:
- first_token_preference: log P(swapped[0]) - log P(clean[0])  -> BINDING (B)
- continuation_preference: mean log P(swapped[1:]) - mean log P(clean[1:]) -> SERIALIZATION (F)
- answer_loss_diff: degradation in semantic answer loss (preservation of R)
- kl_fluency: KL divergence on vocabulary distribution (linguistic coherence control)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from contextlib import AbstractContextManager, nullcontext
from pathlib import Path
from typing import Any

import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.audit_component_hooks import get_layer_components  # noqa: E402
from scripts.run_stage6 import find_transformer_stack  # noqa: E402
from scripts.run_stage7 import load_model, resolve  # noqa: E402
from symbolic_ir.config import load_config  # noqa: E402
from symbolic_ir.mechinterp.patching import _primary, _replace_primary  # noqa: E402
from symbolic_ir.mechinterp.spans import find_after, token_positions_for_char_span  # noqa: E402


class SingleModulePositionRecorder:
    def __init__(self, module: torch.nn.Module, positions: list[int]):
        self.activation = None
        self.positions = positions

        def capture(_module, _inputs, output):
            primary = _primary(output)
            self.activation = primary[0, self.positions, :].detach().cpu()

        self.handle = module.register_forward_hook(capture)

    def close(self):
        self.handle.remove()


class SingleModulePositionPatcher(AbstractContextManager):
    def __init__(self, module: torch.nn.Module, source_activation: torch.Tensor, target_positions: list[int]):
        self.module = module
        self.source_activation = source_activation
        self.target_positions = target_positions
        self.handle = None

    def __enter__(self):
        def patch(_module, _inputs, output):
            primary = _primary(output)
            modified = primary.clone()
            values = self.source_activation.to(device=modified.device, dtype=modified.dtype)
            modified[:, self.target_positions, :] = values.unsqueeze(0).expand(modified.shape[0], -1, -1)
            return _replace_primary(output, modified)

        self.handle = self.module.register_forward_hook(patch)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handle is not None:
            self.handle.remove()
            self.handle = None
        return False


def tokenize_with_spans(tokenizer, text_prompt: str, answer: str, citation_label: str, chat_template_kwargs=None):
    formatted = tokenizer.apply_chat_template(
        [{"role": "user", "content": text_prompt}],
        tokenize=False,
        add_generation_prompt=True,
        **(chat_template_kwargs or {}),
    )
    answer_prefix = f"ANSWER: {answer}\nCITATIONS: "
    full_text = formatted + answer_prefix + citation_label
    
    encoded = tokenizer(full_text, add_special_tokens=False, return_offsets_mapping=True)
    offsets = encoded["offset_mapping"]

    # Locate answer span
    ans_start = len(formatted) + len("ANSWER: ")
    ans_end = ans_start + len(answer)
    ans_positions = token_positions_for_char_span(offsets, ans_start, ans_end)

    # Locate citation target span
    target_start = len(formatted) + len(answer_prefix)
    target_end = len(full_text)
    target_positions = token_positions_for_char_span(offsets, target_start, target_end)

    if not target_positions:
        raise ValueError(f"Target positions empty for citation {citation_label}")

    return {
        "text": full_text,
        "input_ids": encoded["input_ids"],
        "answer_positions": ans_positions,
        "target_positions": target_positions,
        # Positions predicting the citation tokens
        "predicting_positions": [p - 1 for p in target_positions],
        "first_predicting_pos": target_positions[0] - 1,
    }


def find_first_distinguishing_index(clean_tokens: list[int], swapped_tokens: list[int]) -> int:
    """Find the index of the first token where clean and swapped identifiers diverge."""
    for idx in range(min(len(clean_tokens), len(swapped_tokens))):
        if clean_tokens[idx] != swapped_tokens[idx]:
            return idx
    return 0


def compute_metrics(
    model,
    clean_ids: torch.Tensor,
    clean_mask: torch.Tensor,
    clean_target_tokens: list[int],
    swapped_target_tokens: list[int],
    clean_pred_positions: list[int],
    dist_idx: int,
    patcher_context: AbstractContextManager | None = None,
    baseline_first_logits: torch.Tensor | None = None,
    swapped_ids: torch.Tensor | None = None,
    swapped_mask: torch.Tensor | None = None,
    swapped_pred_positions: list[int] | None = None,
    swapped_patcher_context: AbstractContextManager | None = None,
) -> dict[str, Any]:
    context = patcher_context if patcher_context is not None else nullcontext()
    backbone = getattr(model, "model", getattr(model, "language_model", model))
    if hasattr(backbone, "model") and not hasattr(backbone, "layers"):
        backbone = backbone.model

    head = model.get_output_embeddings()

    with context, torch.no_grad():
        # 1. Forward pass on clean sequence (Clean Prompt + Clean Label)
        out_clean = backbone(
            input_ids=clean_ids,
            attention_mask=clean_mask,
            output_hidden_states=False,
            use_cache=False,
            return_dict=True,
        )
        last_hidden_clean = out_clean.last_hidden_state  # [1, seq_len, hidden_dim]
        head_device = head.weight.device if head.weight.device.type != "meta" else last_hidden_clean.device

        # First distinguishing token evaluation (Binding Stage B)
        pred_pos_dist = clean_pred_positions[dist_idx] if dist_idx < len(clean_pred_positions) else clean_pred_positions[0]
        h_first = last_hidden_clean[0, pred_pos_dist:pred_pos_dist + 1, :].to(head_device)
        first_logits = head(h_first)[0].float()
        log_probs_dist = F.log_softmax(first_logits, dim=-1)

        clean_tok_dist = clean_target_tokens[dist_idx]
        swapped_tok_dist = swapped_target_tokens[dist_idx]
        first_clean_logp = float(log_probs_dist[clean_tok_dist].item())
        first_swapped_logp = float(log_probs_dist[swapped_tok_dist].item())
        first_token_pref = first_swapped_logp - first_clean_logp

        # Clean continuation under clean prefix (tokens between dist_idx and closing delimiter)
        clean_cont_logp = None
        if dist_idx + 1 < len(clean_target_tokens) - 1:
            clean_cont_indices = list(range(dist_idx + 1, len(clean_target_tokens) - 1))
            clean_cont_positions = [clean_pred_positions[i] for i in clean_cont_indices]
            h_cont = last_hidden_clean[0, clean_cont_positions, :].to(head_device)
            cont_logits = head(h_cont).float()
            logps = []
            for c_idx, i in enumerate(clean_cont_indices):
                lp = F.log_softmax(cont_logits[c_idx], dim=-1)
                logps.append(float(lp[clean_target_tokens[i]].item()))
            if logps:
                clean_cont_logp = float(sum(logps) / len(logps))

        # Syntax preservation control: log-prob of closing delimiter ']' at final citation position
        syntax_pos = clean_pred_positions[-1]
        syntax_tok = clean_target_tokens[-1]
        h_syntax = last_hidden_clean[0, syntax_pos:syntax_pos + 1, :].to(head_device)
        syntax_logits = head(h_syntax)[0].float()
        syntax_logp = float(F.log_softmax(syntax_logits, dim=-1)[syntax_tok].item())

        # Vocabulary KL Divergence from unpatched baseline (summed over vocabulary in nats)
        kl_div = 0.0
        if baseline_first_logits is not None:
            p_base = F.softmax(baseline_first_logits.to(first_logits.device), dim=-1)
            p_patch = F.log_softmax(first_logits, dim=-1)
            kl_div = float(F.kl_div(p_patch, p_base, reduction="sum", log_target=False).cpu().item())

    # 2. Forward pass on swapped-prefix sequence if continuation tokens exist
    swapped_cont_logp = None
    if swapped_ids is not None and swapped_pred_positions is not None:
        if dist_idx + 1 < len(swapped_target_tokens) - 1:
            sw_ctx = swapped_patcher_context if swapped_patcher_context is not None else nullcontext()
            with sw_ctx, torch.no_grad():
                out_swap = backbone(
                    input_ids=swapped_ids,
                    attention_mask=swapped_mask,
                    output_hidden_states=False,
                    use_cache=False,
                    return_dict=True,
                )
                last_hidden_swap = out_swap.last_hidden_state
                swap_cont_indices = list(range(dist_idx + 1, len(swapped_target_tokens) - 1))
                swap_cont_positions = [swapped_pred_positions[i] for i in swap_cont_indices]
                h_swap_cont = last_hidden_swap[0, swap_cont_positions, :].to(head_device)
                swap_cont_logits = head(h_swap_cont).float()
                s_logps = []
                for s_idx, i in enumerate(swap_cont_indices):
                    lp = F.log_softmax(swap_cont_logits[s_idx], dim=-1)
                    s_logps.append(float(lp[swapped_target_tokens[i]].item()))
                if s_logps:
                    swapped_cont_logp = float(sum(s_logps) / len(s_logps))

    # Candidate own-prefix continuation preference: swapped cont under swapped prefix minus clean cont under clean prefix
    cont_pref = None
    if clean_cont_logp is not None and swapped_cont_logp is not None:
        cont_pref = float(swapped_cont_logp - clean_cont_logp)

    return {
        "first_clean_logp": first_clean_logp,
        "first_swapped_logp": first_swapped_logp,
        "first_token_pref": first_token_pref,
        "clean_cont_own_logp": clean_cont_logp,
        "swapped_cont_own_logp": swapped_cont_logp,
        "cont_pref": cont_pref,
        "syntax_logp": syntax_logp,
        "kl_div": kl_div,
        "raw_first_logits": first_logits.clone().cpu(),
    }


def compute_swap_baseline(
    model,
    direct_swap_ids: torch.Tensor,
    direct_swap_mask: torch.Tensor,
    clean_target_tokens: list[int],
    swapped_target_tokens: list[int],
    swapped_pred_positions: list[int],
    dist_idx: int,
    clean_base_cont_logp: float | None = None,
) -> dict[str, Any]:
    backbone = getattr(model, "model", getattr(model, "language_model", model))
    if hasattr(backbone, "model") and not hasattr(backbone, "layers"):
        backbone = backbone.model

    head = model.get_output_embeddings()

    with torch.no_grad():
        out = backbone(
            input_ids=direct_swap_ids,
            attention_mask=direct_swap_mask,
            output_hidden_states=False,
            use_cache=False,
            return_dict=True,
        )
        last_hidden = out.last_hidden_state
        head_device = head.weight.device if head.weight.device.type != "meta" else last_hidden.device

        # First distinguishing token evaluation
        pred_pos_dist = swapped_pred_positions[dist_idx] if dist_idx < len(swapped_pred_positions) else swapped_pred_positions[0]
        h_first = last_hidden[0, pred_pos_dist:pred_pos_dist + 1, :].to(head_device)
        first_logits = head(h_first)[0].float()
        log_probs_dist = F.log_softmax(first_logits, dim=-1)

        clean_tok_dist = clean_target_tokens[dist_idx]
        swapped_tok_dist = swapped_target_tokens[dist_idx]
        first_clean_logp = float(log_probs_dist[clean_tok_dist].item())
        first_swapped_logp = float(log_probs_dist[swapped_tok_dist].item())
        first_token_pref = first_swapped_logp - first_clean_logp

        # Swapped continuation tokens under swapped prefix
        swapped_cont_logp = None
        if dist_idx + 1 < len(swapped_target_tokens) - 1:
            swap_cont_indices = list(range(dist_idx + 1, len(swapped_target_tokens) - 1))
            swap_cont_positions = [swapped_pred_positions[i] for i in swap_cont_indices]
            h_cont = last_hidden[0, swap_cont_positions, :].to(head_device)
            cont_logits = head(h_cont).float()
            logps = []
            for s_idx, i in enumerate(swap_cont_indices):
                lp = F.log_softmax(cont_logits[s_idx], dim=-1)
                logps.append(float(lp[swapped_target_tokens[i]].item()))
            if logps:
                swapped_cont_logp = float(sum(logps) / len(logps))

        # Syntax log-prob of closing delimiter
        syntax_pos = swapped_pred_positions[-1]
        syntax_tok = swapped_target_tokens[-1]
        h_syntax = last_hidden[0, syntax_pos:syntax_pos + 1, :].to(head_device)
        syntax_logits = head(h_syntax)[0].float()
        syntax_logp = float(F.log_softmax(syntax_logits, dim=-1)[syntax_tok].item())

    cont_pref = None
    if clean_base_cont_logp is not None and swapped_cont_logp is not None:
        cont_pref = float(swapped_cont_logp - clean_base_cont_logp)

    return {
        "first_clean_logp": first_clean_logp,
        "first_swapped_logp": first_swapped_logp,
        "first_token_pref": first_token_pref,
        "clean_cont_own_logp": clean_base_cont_logp,
        "swapped_cont_own_logp": swapped_cont_logp,
        "cont_pref": cont_pref,
        "syntax_logp": syntax_logp,
        "kl_div": 0.0,
    }


def run_decomposition(
    config_path: Path,
    dataset_path: Path,
    output_path: Path,
    layers: list[int] | None = None,
    max_cases: int | None = None,
):
    print(f"\n{'='*70}\nRunning Component Decomposition on {config_path.name}\n{'='*70}")
    config = load_config(resolve(config_path))
    model, tokenizer = load_model(config)

    all_layers, _ = find_transformer_stack(model)
    total_layers = len(all_layers)

    if layers is None:
        cfg_cand = config.generation.get("candidate_layers")
        if cfg_cand:
            layers = [int(l) for l in cfg_cand]
        elif total_layers == 28:  # Qwen 2.5
            layers = [1, 12, 18, 20, 22, 24, 26, 28]
        elif total_layers == 24:  # Qwen 3.5 2B
            layers = [1, 8, 12, 14, 16, 18, 20, 24]
        else:
            layers = [1, total_layers // 4, total_layers // 2, 3 * total_layers // 4, total_layers]

    print(f"Intervention layers to evaluate ({len(layers)}): {layers}")

    # Load cases
    raw_lines = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if max_cases:
        raw_lines = raw_lines[:max_cases]
    print(f"Loaded {len(raw_lines)} cases from {dataset_path}")

    device = next(model.parameters()).device
    chat_kwargs = config.generation.get("chat_template_kwargs")
    backbone = getattr(model, "model", getattr(model, "language_model", model))
    if hasattr(backbone, "model") and not hasattr(backbone, "layers"):
        backbone = backbone.model

    records = []
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Resume capability: check already completed cases
    completed_case_keys = set()
    if output_path.exists():
        for line in output_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    c_rec = json.loads(line)
                    completed_case_keys.add((c_rec["example_id"], c_rec["condition"]))
                except Exception:
                    pass
    if completed_case_keys:
        print(f"Resuming: found {len(completed_case_keys)} already completed cases in {output_path.name}")

    out_file = output_path.open("a", encoding="utf-8")

    try:
        for case_idx, case in enumerate(raw_lines):
            case_key = (case["example_id"], case["condition"])
            if case_key in completed_case_keys:
                continue

            condition = case["condition"]
            clean_text_obj = tokenize_with_spans(tokenizer, case["clean_prompt"], case["answer"], case["clean_label"], chat_kwargs)
            swapped_text_obj = tokenize_with_spans(tokenizer, case["swapped_prompt"], case["answer"], case["swapped_label"], chat_kwargs)
            clean_with_swapped_obj = tokenize_with_spans(tokenizer, case["clean_prompt"], case["answer"], case["swapped_label"], chat_kwargs)

            clean_ids = torch.tensor([clean_text_obj["input_ids"]], device=device)
            clean_mask = torch.ones_like(clean_ids)
            direct_swap_ids = torch.tensor([swapped_text_obj["input_ids"]], device=device)
            direct_swap_mask = torch.ones_like(direct_swap_ids)
            clean_with_swapped_ids = torch.tensor([clean_with_swapped_obj["input_ids"]], device=device)
            clean_with_swapped_mask = torch.ones_like(clean_with_swapped_ids)

            clean_target_tokens = [clean_text_obj["input_ids"][p] for p in clean_text_obj["target_positions"]]
            swapped_target_tokens = [swapped_text_obj["input_ids"][p] for p in swapped_text_obj["target_positions"]]

            pred_positions = clean_text_obj["predicting_positions"]
            swapped_pred_positions = swapped_text_obj["predicting_positions"]
            clean_with_swapped_pred_positions = clean_with_swapped_obj["predicting_positions"]

            dist_idx = find_first_distinguishing_index(clean_target_tokens, swapped_target_tokens)
            has_continuation = (dist_idx + 1 < len(clean_target_tokens) - 1) and (dist_idx + 1 < len(swapped_target_tokens) - 1)

            # 1. Unpatched Clean Baseline
            clean_base = compute_metrics(
                model=model,
                clean_ids=clean_ids,
                clean_mask=clean_mask,
                clean_target_tokens=clean_target_tokens,
                swapped_target_tokens=swapped_target_tokens,
                clean_pred_positions=pred_positions,
                dist_idx=dist_idx,
                swapped_ids=clean_with_swapped_ids if has_continuation else None,
                swapped_mask=clean_with_swapped_mask if has_continuation else None,
                swapped_pred_positions=clean_with_swapped_pred_positions if has_continuation else None,
            )
            base_first_logits = clean_base.pop("raw_first_logits")

            # 2. Counterfactual Swap Upper Bound (no patch, evaluate swapped prompt)
            swap_base = compute_swap_baseline(
                model=model,
                direct_swap_ids=direct_swap_ids,
                direct_swap_mask=direct_swap_mask,
                clean_target_tokens=clean_target_tokens,
                swapped_target_tokens=swapped_target_tokens,
                swapped_pred_positions=swapped_pred_positions,
                dist_idx=dist_idx,
                clean_base_cont_logp=clean_base["clean_cont_own_logp"],
            )

            # Baseline direct swap shifts
            base_shift_first = swap_base["first_token_pref"] - clean_base["first_token_pref"]
            base_shift_cont = (swap_base["cont_pref"] - clean_base["cont_pref"]) if (has_continuation and swap_base["cont_pref"] is not None and clean_base["cont_pref"] is not None) else None

            case_record = {
                "case_idx": case_idx,
                "example_id": case["example_id"],
                "condition": condition,
                "task_type": case["task_type"],
                "num_sources": case["num_sources"],
                "clean_label": case["clean_label"],
                "swapped_label": case["swapped_label"],
                "dist_idx": dist_idx,
                "has_continuation": has_continuation,
                "base_shift_first": round(base_shift_first, 4),
                "base_shift_cont": round(base_shift_cont, 4) if base_shift_cont is not None else None,
                "clean_baseline": clean_base,
                "swap_baseline": swap_base,
                "layer_results": {},
            }

            # Nested context for multiple patchers
            class MultiContext(AbstractContextManager):
                def __init__(self, ctx_list):
                    self.ctx_list = ctx_list
                def __enter__(self):
                    for c in self.ctx_list:
                        c.__enter__()
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    for c in reversed(self.ctx_list):
                        c.__exit__(exc_type, exc_val, exc_tb)
                    return False

            # Record donor activations across all candidate layers in a single donor forward pass
            donor_activations = {}
            recorders = []
            for l_num in layers:
                comp = get_layer_components(all_layers[l_num - 1])
                m_mod = comp["mixer"]["out_proj"] if comp["mixer"]["out_proj"] else comp["mixer"]["module"]
                mlp_mod = comp["mlp"]["out_proj"] if comp["mlp"]["out_proj"] else comp["mlp"]["module"]
                r_m = SingleModulePositionRecorder(m_mod, swapped_pred_positions)
                r_mlp = SingleModulePositionRecorder(mlp_mod, swapped_pred_positions)
                recorders.append((l_num, r_m, r_mlp))

            try:
                with torch.inference_mode():
                    backbone(input_ids=direct_swap_ids, attention_mask=direct_swap_mask, use_cache=False, return_dict=True)
                for l_num, r_m, r_mlp in recorders:
                    donor_activations[l_num] = {
                        "mixer": r_m.activation,
                        "mlp": r_mlp.activation,
                    }
            finally:
                for _, r_m, r_mlp in recorders:
                    r_m.close()
                    r_mlp.close()

            # For each layer, run Mixer patch, MLP patch, and Joint Layer patch
            for layer_num in layers:
                layer = all_layers[layer_num - 1]
                comp_info = get_layer_components(layer)
                mixer_mod = comp_info["mixer"]["out_proj"] if comp_info["mixer"]["out_proj"] else comp_info["mixer"]["module"]
                mlp_mod = comp_info["mlp"]["out_proj"] if comp_info["mlp"]["out_proj"] else comp_info["mlp"]["module"]

                act_mixer = donor_activations[layer_num]["mixer"]
                act_mlp = donor_activations[layer_num]["mlp"]

                layer_res = {}

                # Interventions: "mixer", "mlp", "both"
                for intervention_type in ["mixer", "mlp", "both"]:
                    # Recipient run 1 (clean prompt + clean label): patch donor activations at pred_positions
                    patch_len = min(len(pred_positions), len(swapped_pred_positions))
                    patchers_clean = []
                    if intervention_type in ("mixer", "both"):
                        patchers_clean.append(SingleModulePositionPatcher(mixer_mod, act_mixer[:patch_len], pred_positions[:patch_len]))
                    if intervention_type in ("mlp", "both"):
                        patchers_clean.append(SingleModulePositionPatcher(mlp_mod, act_mlp[:patch_len], pred_positions[:patch_len]))

                    # Recipient run 2 (clean prompt + swapped label): patch donor activations at clean_with_swapped_pred_positions
                    patchers_swapped = []
                    if has_continuation:
                        patch_len_sw = min(len(clean_with_swapped_pred_positions), len(swapped_pred_positions))
                        if intervention_type in ("mixer", "both"):
                            patchers_swapped.append(SingleModulePositionPatcher(mixer_mod, act_mixer[:patch_len_sw], clean_with_swapped_pred_positions[:patch_len_sw]))
                        if intervention_type in ("mlp", "both"):
                            patchers_swapped.append(SingleModulePositionPatcher(mlp_mod, act_mlp[:patch_len_sw], clean_with_swapped_pred_positions[:patch_len_sw]))

                    m_ctx_clean = MultiContext(patchers_clean)
                    m_ctx_swapped = MultiContext(patchers_swapped) if has_continuation else None

                    patched_metrics = compute_metrics(
                        model=model,
                        clean_ids=clean_ids,
                        clean_mask=clean_mask,
                        clean_target_tokens=clean_target_tokens,
                        swapped_target_tokens=swapped_target_tokens,
                        clean_pred_positions=pred_positions,
                        dist_idx=dist_idx,
                        patcher_context=m_ctx_clean,
                        baseline_first_logits=base_first_logits,
                        swapped_ids=clean_with_swapped_ids if has_continuation else None,
                        swapped_mask=clean_with_swapped_mask if has_continuation else None,
                        swapped_pred_positions=clean_with_swapped_pred_positions if has_continuation else None,
                        swapped_patcher_context=m_ctx_swapped,
                    )
                    patched_metrics.pop("raw_first_logits")

                    # Absolute causal shifts
                    abs_shift_first = patched_metrics["first_token_pref"] - clean_base["first_token_pref"]
                    patched_metrics["abs_shift_first"] = round(abs_shift_first, 4)

                    # Compute recovery percentages with denominator guards
                    recov_first = (abs_shift_first / base_shift_first) if abs(base_shift_first) > 0.5 else None
                    patched_metrics["recovery_first_pct"] = round(recov_first * 100, 2) if recov_first is not None else None

                    if has_continuation and base_shift_cont is not None and patched_metrics["cont_pref"] is not None and clean_base["cont_pref"] is not None:
                        abs_shift_cont = patched_metrics["cont_pref"] - clean_base["cont_pref"]
                        patched_metrics["abs_shift_cont"] = round(abs_shift_cont, 4)
                        recov_cont = (abs_shift_cont / base_shift_cont) if abs(base_shift_cont) > 0.5 else None
                        patched_metrics["recovery_cont_pct"] = round(recov_cont * 100, 2) if recov_cont is not None else None
                    else:
                        patched_metrics["abs_shift_cont"] = None
                        patched_metrics["recovery_cont_pct"] = None

                    # Syntax preservation change
                    syntax_shift = patched_metrics["syntax_logp"] - clean_base["syntax_logp"]
                    patched_metrics["syntax_shift"] = round(syntax_shift, 4)

                    layer_res[intervention_type] = patched_metrics

                case_record["layer_results"][str(layer_num)] = layer_res

            # Write record immediately and flush
            out_file.write(json.dumps(case_record) + "\n")
            out_file.flush()
            records.append(case_record)

            if (case_idx + 1) % 4 == 0 or case_idx == len(raw_lines) - 1:
                print(f"  Processed {case_idx + 1}/{len(raw_lines)} cases...", flush=True)

            # Free CUDA cache between cases
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    finally:
        out_file.close()

    print(f"Completed run. Output written to: {output_path}")
    return records


def main():
    parser = argparse.ArgumentParser(description="Run component decomposition")
    parser.add_argument("--config", default="configs/experiments/stage7_qwen25_15b.yaml")
    parser.add_argument("--dataset", default="data/circuit/discovery_n32.jsonl")
    parser.add_argument("--output", default="results/circuit/qwen25_15b_decomposition.jsonl")
    parser.add_argument("--layers", nargs="+", type=int, default=None)
    parser.add_argument("--max-cases", type=int, default=None)
    args = parser.parse_args()

    run_decomposition(
        config_path=ROOT / args.config,
        dataset_path=ROOT / args.dataset,
        output_path=ROOT / args.output,
        layers=args.layers,
        max_cases=args.max_cases,
    )


if __name__ == "__main__":
    main()

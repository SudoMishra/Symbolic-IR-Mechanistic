#!/usr/bin/env python3
"""Phase 4: Head-Level Circuit Localization.

Within the discovered causal attention layers (e.g., Layer 20),
isolates and patches individual attention heads to identify the exact
binding heads responsible for source-identifier routing.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from contextlib import AbstractContextManager, nullcontext
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.audit_component_hooks import get_layer_components  # noqa: E402
from scripts.run_circuit_decomposition import (  # noqa: E402
    compute_metrics,
    find_first_distinguishing_index,
    tokenize_with_spans,
)
from scripts.run_stage6 import find_transformer_stack  # noqa: E402
from scripts.run_stage7 import load_model, resolve  # noqa: E402
from symbolic_ir.config import load_config  # noqa: E402


class SingleHeadRecorder:
    def __init__(self, o_proj_module: torch.nn.Module, head_idx: int, head_dim: int, positions: list[int]):
        self.activation = None
        self.head_idx = head_idx
        self.head_dim = head_dim
        self.positions = positions

        def capture(_module, inputs):
            tensor = inputs[0]  # [B, S, H * D_h]
            start_col = head_idx * head_dim
            end_col = (head_idx + 1) * head_dim
            self.activation = tensor[0, self.positions, start_col:end_col].detach().cpu()

        self.handle = o_proj_module.register_forward_pre_hook(capture)

    def close(self):
        self.handle.remove()


class SingleHeadPatcher(AbstractContextManager):
    def __init__(self, o_proj_module: torch.nn.Module, head_idx: int, head_dim: int, source_head_act: torch.Tensor, target_positions: list[int]):
        self.head_idx = head_idx
        self.head_dim = head_dim
        self.source_head_act = source_head_act
        self.target_positions = target_positions

        def patch(_module, inputs):
            tensor = inputs[0]
            modified = tensor.clone()
            start_col = head_idx * head_dim
            end_col = (head_idx + 1) * head_dim
            vals = self.source_head_act.to(device=modified.device, dtype=modified.dtype)
            modified[:, self.target_positions, start_col:end_col] = vals.unsqueeze(0).expand(modified.shape[0], -1, -1)
            return (modified,)

        self.handle = o_proj_module.register_forward_pre_hook(patch)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.handle.remove()
        return False


def run_head_localization(
    config_path: Path,
    dataset_path: Path,
    output_path: Path,
    layer_num: int = 20,
    max_cases: int | None = None,
):
    print(f"\n{'='*70}\nRunning Head-Level Localization on {config_path.name} (Layer {layer_num})\n{'='*70}")
    config = load_config(resolve(config_path))
    model, tokenizer = load_model(config)

    all_layers, _ = find_transformer_stack(model)
    target_layer = all_layers[layer_num - 1]

    # Check that layer has standard self_attn.o_proj
    if not hasattr(target_layer, "self_attn") or not hasattr(target_layer.self_attn, "o_proj"):
        raise ValueError(f"Layer {layer_num} does not have self_attn.o_proj for head slicing")

    o_proj = target_layer.self_attn.o_proj
    num_heads = target_layer.self_attn.config.num_attention_heads
    hidden_size = target_layer.self_attn.config.hidden_size
    head_dim = getattr(target_layer.self_attn, "head_dim", hidden_size // num_heads)

    print(f"Layer {layer_num}: {num_heads} attention heads, head_dim={head_dim}")

    raw_lines = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if max_cases:
        raw_lines = raw_lines[:max_cases]
    print(f"Loaded {len(raw_lines)} cases from {dataset_path.name}")

    device = next(model.parameters()).device
    chat_kwargs = config.generation.get("chat_template_kwargs")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_file = output_path.open("w", encoding="utf-8")

    try:
        for case_idx, case in enumerate(raw_lines):
            clean_text_obj = tokenize_with_spans(tokenizer, case["clean_prompt"], case["answer"], case["clean_label"], chat_kwargs)
            swapped_text_obj = tokenize_with_spans(tokenizer, case["swapped_prompt"], case["answer"], case["swapped_label"], chat_kwargs)

            clean_ids = torch.tensor([clean_text_obj["input_ids"]], device=device)
            clean_mask = torch.ones_like(clean_ids)
            swapped_ids = torch.tensor([swapped_text_obj["input_ids"]], device=device)
            swapped_mask = torch.ones_like(swapped_ids)

            clean_target_tokens = tokenizer.encode(case["clean_label"], add_special_tokens=False)
            swapped_target_tokens = tokenizer.encode(case["swapped_label"], add_special_tokens=False)

            pred_positions = clean_text_obj["predicting_positions"]
            swapped_pred_positions = swapped_text_obj["predicting_positions"]

            common_len = min(len(pred_positions), len(swapped_pred_positions))
            pred_positions = pred_positions[:common_len]
            swapped_pred_positions = swapped_pred_positions[:common_len]
            clean_target_tokens = clean_target_tokens[:common_len]
            swapped_target_tokens = swapped_target_tokens[:common_len]

            # Baselines
            clean_base = compute_metrics(
                model, clean_ids, clean_mask,
                clean_target_tokens, swapped_target_tokens,
                pred_positions, clean_text_obj["answer_positions"]
            )
            base_first_logits = clean_base.pop("raw_first_logits")

            swap_base = compute_metrics(
                model, swapped_ids, swapped_mask,
                clean_target_tokens, swapped_target_tokens,
                swapped_pred_positions, swapped_text_obj["answer_positions"]
            )
            swap_base.pop("raw_first_logits")

            denom_first = swap_base["first_token_pref"] - clean_base["first_token_pref"]

            case_record = {
                "case_idx": case_idx,
                "example_id": case["example_id"],
                "condition": case["condition"],
                "clean_baseline": clean_base,
                "swap_baseline": swap_base,
                "layer": layer_num,
                "head_results": {},
            }

            # Intervene on each head h
            for h in range(num_heads):
                # Donor run
                recorder = SingleHeadRecorder(o_proj, h, head_dim, swapped_pred_positions)
                try:
                    with torch.inference_mode():
                        model(input_ids=swapped_ids, attention_mask=swapped_mask)
                finally:
                    recorder.close()

                # Recipient run
                patcher = SingleHeadPatcher(o_proj, h, head_dim, recorder.activation, pred_positions)
                patched_metrics = compute_metrics(
                    model, clean_ids, clean_mask,
                    clean_target_tokens, swapped_target_tokens,
                    pred_positions, clean_text_obj["answer_positions"],
                    patcher_context=patcher,
                    baseline_first_logits=base_first_logits,
                )
                patched_metrics.pop("raw_first_logits")

                # Recovery %
                recov = (patched_metrics["first_token_pref"] - clean_base["first_token_pref"]) / denom_first if abs(denom_first) > 0.5 else None
                patched_metrics["recovery_first_pct"] = round(recov * 100, 2) if recov is not None else None
                patched_metrics["abs_shift_first"] = patched_metrics["first_token_pref"] - clean_base["first_token_pref"]

                case_record["head_results"][str(h)] = patched_metrics

            out_file.write(json.dumps(case_record) + "\n")
            out_file.flush()

            if (case_idx + 1) % 4 == 0 or case_idx == len(raw_lines) - 1:
                print(f"  Processed {case_idx + 1}/{len(raw_lines)} cases...", flush=True)

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    finally:
        out_file.close()

    print(f"Head localization complete. Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run head-level localization")
    parser.add_argument("--config", default="configs/experiments/stage7_qwen25_15b.yaml")
    parser.add_argument("--dataset", default="data/circuit/discovery_n32.jsonl")
    parser.add_argument("--output", default="results/circuit/qwen25_head_scores_l20.jsonl")
    parser.add_argument("--layer", type=int, default=20)
    parser.add_argument("--max-cases", type=int, default=12)
    args = parser.parse_args()

    run_head_localization(
        config_path=ROOT / args.config,
        dataset_path=ROOT / args.dataset,
        output_path=ROOT / args.output,
        layer_num=args.layer,
        max_cases=args.max_cases,
    )


if __name__ == "__main__":
    main()

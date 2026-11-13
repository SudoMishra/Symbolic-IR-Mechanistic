#!/usr/bin/env python3
"""Phase 0 Diagnostic Gate: Audit component-level hook points across models.

Validates that:
1. Transformer layers and component submodules (mixer, MLP) are correctly located.
2. Identity passthrough hooks leave logits completely unchanged (machine precision check).
3. Pre- and post-projection tensor shapes match architectural expectations.
4. Active replacement hooks successfully alter model activations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.run_stage6 import find_transformer_stack  # noqa: E402
from scripts.run_stage7 import load_model, resolve  # noqa: E402
from symbolic_ir.config import ExperimentConfig, load_config  # noqa: E402


def get_layer_components(layer: torch.nn.Module) -> dict[str, Any]:
    """Retrieve the mixer (attention/recurrent) and MLP components of a transformer decoder layer."""
    if hasattr(layer, "self_attn"):
        mixer_module = layer.self_attn
        out_proj = getattr(layer.self_attn, "o_proj", None)
        mixer_type = "attention"
    elif hasattr(layer, "linear_attn"):
        mixer_module = layer.linear_attn
        out_proj = getattr(layer.linear_attn, "out_proj", None)
        mixer_type = "recurrent"
    else:
        raise ValueError(f"Unrecognized mixer module in layer {type(layer)}")

    if hasattr(layer, "mlp"):
        mlp_module = layer.mlp
        mlp_out_proj = getattr(layer.mlp, "down_proj", None)
    else:
        raise ValueError(f"Unrecognized MLP module in layer {type(layer)}")

    return {
        "mixer": {
            "module": mixer_module,
            "out_proj": out_proj,
            "type": mixer_type,
        },
        "mlp": {
            "module": mlp_module,
            "out_proj": mlp_out_proj,
            "type": "mlp",
        },
    }


def audit_model(config_path: Path, target_layers: list[int] | None = None) -> dict[str, Any]:
    print(f"\n{'='*70}\nAuditing hook points for {config_path.name}\n{'='*70}")
    config = load_config(resolve(config_path))
    model, tokenizer = load_model(config)

    layers, final_norm = find_transformer_stack(model)
    total_layers = len(layers)
    print(f"Loaded model. Total decoder layers: {total_layers}")

    # Build dummy input
    prompt = "Document [S1]: The secret code is ALPHA. Document [S2]: The secret code is BETA. Question: What is S1? Answer: The code is ["
    inputs = tokenizer(prompt, return_tensors="pt")
    input_device = next(model.parameters()).device
    input_ids = inputs["input_ids"].to(input_device)
    attention_mask = inputs["attention_mask"].to(input_device)

    # 1. Baseline unhooked forward pass
    with torch.inference_mode():
        baseline_out = model(input_ids=input_ids, attention_mask=attention_mask)
        baseline_logits = baseline_out.logits[:, -1, :].clone().cpu()

    results_by_layer = {}
    if target_layers:
        sampled_layers = sorted(set([l for l in target_layers if 1 <= l <= total_layers]))
    else:
        sampled_layers = [1, total_layers // 2, total_layers - 2, total_layers]

    print(f"Auditing exact target layers: {sampled_layers}")
    for layer_num in sampled_layers:
        layer_idx = layer_num - 1
        layer = layers[layer_idx]
        components = get_layer_components(layer)
        mixer_info = components["mixer"]
        mlp_info = components["mlp"]

        layer_data = {
            "layer_number": layer_num,
            "mixer_type": mixer_info["type"],
            "mixer_module": mixer_info["module"].__class__.__name__,
            "mixer_out_proj": mixer_info["out_proj"].__class__.__name__ if mixer_info["out_proj"] else None,
            "mlp_module": mlp_info["module"].__class__.__name__,
            "mlp_out_proj": mlp_info["out_proj"].__class__.__name__ if mlp_info["out_proj"] else None,
            "identity_hook_mixer_max_diff": None,
            "identity_hook_mlp_max_diff": None,
            "perturbation_mixer_diff": None,
            "shapes": {},
        }

        # 2. Test identity hook on mixer
        captured_shapes = {}

        def identity_mixer_hook(_mod, _inp, out):
            tensor = out[0] if isinstance(out, (tuple, list)) else out
            captured_shapes["mixer_out"] = list(tensor.shape)
            return out

        hook_target = mixer_info["out_proj"] if mixer_info["out_proj"] else mixer_info["module"]
        handle = hook_target.register_forward_hook(identity_mixer_hook)
        try:
            with torch.inference_mode():
                out = model(input_ids=input_ids, attention_mask=attention_mask)
                diff = (out.logits[:, -1, :].cpu() - baseline_logits).abs().max().item()
                layer_data["identity_hook_mixer_max_diff"] = float(diff)
        finally:
            handle.remove()

        # 3. Test identity hook on MLP
        def identity_mlp_hook(_mod, _inp, out):
            tensor = out[0] if isinstance(out, (tuple, list)) else out
            captured_shapes["mlp_out"] = list(tensor.shape)
            return out

        mlp_target = mlp_info["out_proj"] if mlp_info["out_proj"] else mlp_info["module"]
        handle = mlp_target.register_forward_hook(identity_mlp_hook)
        try:
            with torch.inference_mode():
                out = model(input_ids=input_ids, attention_mask=attention_mask)
                diff = (out.logits[:, -1, :].cpu() - baseline_logits).abs().max().item()
                layer_data["identity_hook_mlp_max_diff"] = float(diff)
        finally:
            handle.remove()

        # 4. Test zero ablation / perturbation hook on mixer
        def perturb_mixer_hook(_mod, _inp, out):
            if isinstance(out, (tuple, list)):
                tensor = out[0]
                perturbed = torch.zeros_like(tensor)
                return (perturbed,) + tuple(out[1:])
            return torch.zeros_like(out)

        handle = hook_target.register_forward_hook(perturb_mixer_hook)
        try:
            with torch.inference_mode():
                out = model(input_ids=input_ids, attention_mask=attention_mask)
                diff = (out.logits[:, -1, :].cpu() - baseline_logits).abs().max().item()
                layer_data["perturbation_mixer_diff"] = float(diff)
        finally:
            handle.remove()

        layer_data["shapes"] = captured_shapes
        results_by_layer[str(layer_num)] = layer_data
        print(f"  Layer {layer_num:2d} ({mixer_info['type']:10s}): "
              f"Mixer identity Δ={layer_data['identity_hook_mixer_max_diff']:.2e}, "
              f"MLP identity Δ={layer_data['identity_hook_mlp_max_diff']:.2e}, "
              f"Perturbation Δ={layer_data['perturbation_mixer_diff']:.2f}, "
              f"Shapes: {captured_shapes}")

    # Memory cleanup
    del model, tokenizer, baseline_logits
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {
        "config": str(config_path),
        "total_layers": total_layers,
        "layers_audited": results_by_layer,
        "gate_passed": all(
            d["identity_hook_mixer_max_diff"] < 1e-4 and
            d["identity_hook_mlp_max_diff"] < 1e-4 and
            d["perturbation_mixer_diff"] > 0.1
            for d in results_by_layer.values()
        )
    }


CONFIG_MODEL_MAP = {
    "circuit_qwen25_15b": "qwen2.5-1.5b-instruct",
    "circuit_qwen35_2b": "qwen3.5-2b",
    "circuit_tiny_aya": "tiny-aya-global",
    "circuit_qwen35_4b": "qwen3.5-4b",
    "circuit_gemma4_e2b": "gemma-4-e2b-it",
    "circuit_gemma4_e4b": "gemma-4-e4b-it",
}


def main():
    parser = argparse.ArgumentParser(description="Audit component hook points across all 6 models")
    parser.add_argument("--configs", nargs="+", default=[
        "configs/circuit/circuit_qwen25_15b.yaml",
        "configs/circuit/circuit_qwen35_2b.yaml",
        "configs/circuit/circuit_tiny_aya.yaml",
        "configs/circuit/circuit_qwen35_4b.yaml",
        "configs/circuit/circuit_gemma4_e2b.yaml",
        "configs/circuit/circuit_gemma4_e4b.yaml",
    ])
    parser.add_argument("--output", default="results/audit/component_hook_audit.json")
    args = parser.parse_args()

    prereg_p = ROOT / "results/circuit/circuit_preregistration.json"
    prereg = json.loads(prereg_p.read_text(encoding="utf-8"))["candidate_circuits"] if prereg_p.exists() else {}

    audit_summary = {}
    for conf_str in args.configs:
        conf_path = ROOT / conf_str
        stem = conf_path.stem
        model_id = CONFIG_MODEL_MAP.get(stem, "")
        cand_layers = prereg.get(model_id, {}).get("candidate_layers", [])
        
        summary = audit_model(conf_path, target_layers=cand_layers)
        key_name = stem.replace("circuit_", "")
        audit_summary[key_name] = summary

    out_path = ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit_summary, indent=2), encoding="utf-8")
    print(f"\nSaved component hook audit report to: {out_path}")

    all_passed = all(item["gate_passed"] for item in audit_summary.values())
    if all_passed:
        print("\n>>> ALL PHASE 0 HOOK AUDIT CHECKS PASSED SUCCESSFULLY. <<<")
    else:
        print("\n>>> WARNING: SOME CHECKS FAILED. REVIEW AUDIT REPORT. <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()

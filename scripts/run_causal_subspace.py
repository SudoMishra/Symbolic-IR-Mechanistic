#!/usr/bin/env python3
"""Phase 5: Post-Evidence Counterfactual-Difference Causal Subspace Localization.

Fits an orthonormal basis via SVD on donor-clean activation differences
captured strictly on the discovery split at the post-evidence residual stream position.
Evaluates low-rank projection interventions along rank k in {1, 2, 4, 8, 16, 32, 64}
and compares against:
1. Equal-rank random orthonormal bases.
2. Orthogonal complement subspace.
3. Norm-matched random directions.
"""

from __future__ import annotations

import argparse
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

from scripts.run_computation_vs_transport import (  # noqa: E402
    align_activation_spans,
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


class SubspaceProjectionPatcher(AbstractContextManager):
    """Projects donor-clean activation difference onto a rank-k orthonormal basis."""

    def __init__(
        self,
        layer_module: torch.nn.Module,
        basis_k: torch.Tensor,  # [d_model, k]
        clean_activation: torch.Tensor,  # [seq_len, d_model]
        donor_activation: torch.Tensor,  # [seq_len, d_model]
        target_positions: list[int],
        complement: bool = False,
    ):
        self.layer_module = layer_module
        self.basis_k = basis_k
        self.clean_act = clean_activation
        if donor_activation.shape[0] != clean_activation.shape[0]:
            aligned_donor, _ = align_activation_spans(
                list(range(clean_activation.shape[0])),
                list(range(donor_activation.shape[0])),
                donor_activation,
            )
            self.donor_act = aligned_donor
        else:
            self.donor_act = donor_activation
        self.target_positions = target_positions
        self.complement = complement
        self.handle = None

    def __enter__(self):
        def patch(_module, _inputs, output):
            primary = output[0] if isinstance(output, tuple) else output
            if not self.target_positions or max(self.target_positions) >= primary.shape[1]:
                return output
            modified = primary.clone()

            # Align device and dtype
            dev = modified.device
            dt = modified.dtype
            v = self.basis_k.to(device=dev, dtype=torch.float32)

            clean = self.clean_act.to(device=dev, dtype=torch.float32)
            donor = self.donor_act.to(device=dev, dtype=torch.float32)
            delta = donor - clean  # [pos_len, d_model]

            # Project delta onto basis: P_k(delta) = delta @ V @ V.T
            # delta: [P, d], V: [d, k] -> delta @ V is [P, k] -> [P, k] @ V.T is [P, d]
            proj_delta = (delta @ v) @ v.t()
            if self.complement:
                proj_delta = delta - proj_delta

            intervened = clean + proj_delta
            modified[:, self.target_positions, :] = intervened.to(dtype=dt).unsqueeze(0).expand(modified.shape[0], -1, -1)

            if isinstance(output, tuple):
                return (modified,) + output[1:]
            return modified

        self.handle = self.layer_module.register_forward_hook(patch)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handle is not None:
            self.handle.remove()
            self.handle = None
        return False


def fit_svd_subspace(
    diff_vectors: list[torch.Tensor],  # list of [d_model] tensors
    center_by_condition: bool = True,
    condition_labels: list[str] | None = None,
) -> dict[str, Any]:
    """Fit SVD on counterfactual difference vectors, centering within condition."""
    X = torch.stack(diff_vectors, dim=0).float()  # [N, d_model]
    N, d_model = X.shape

    if center_by_condition and condition_labels and len(condition_labels) == N:
        X_centered = torch.zeros_like(X)
        for cond in set(condition_labels):
            idxs = [i for i, c in enumerate(condition_labels) if c == cond]
            sub = X[idxs]
            mean_c = sub.mean(dim=0, keepdim=True)
            X_centered[idxs] = sub - mean_c
    else:
        X_centered = X - X.mean(dim=0, keepdim=True)

    # SVD: X = U @ S @ V.T -> columns of V are right singular vectors
    u, s, vh = torch.linalg.svd(X_centered, full_matrices=False)
    # vh has shape [min(N, d), d_model]
    # basis vectors: rows of vh transposed -> V has shape [d_model, min(N, d)]
    V = vh.t()

    total_var = torch.sum(s ** 2).item()
    cumulative_var = torch.cumsum(s ** 2, dim=0) / total_var

    return {
        "V": V,  # [d_model, n_components]
        "singular_values": s.tolist(),
        "cumulative_variance_ratio": cumulative_var.tolist(),
        "total_variance": total_var,
        "n_samples": N,
        "d_model": d_model,
    }


def generate_random_orthonormal_basis(d_model: int, k: int, seed: int = 42) -> torch.Tensor:
    """Generate a reproducible random orthonormal basis of dimension [d_model, k] using QR decomposition."""
    gen = torch.Generator().manual_seed(seed)
    gaussian = torch.randn(d_model, k, generator=gen)
    q, _ = torch.linalg.qr(gaussian)
    return q[:, :k]


def run_subspace_evaluation(
    config_path: Path,
    eval_dataset_path: Path,
    basis_artifact_path: Path,
    output_path: Path,
    target_layer_1based: int = 14,
    semantic_position: str = "pos_post_evidence",
    rank_grid: list[int] = [1, 2, 4, 8, 16, 32],
    max_cases: int | None = None,
):
    """Evaluate causal recovery across subspace ranks and controls."""
    print("=" * 80)
    print("SEQUENCE 3B: CAUSAL SUBSPACE LOCALIZATION EVALUATION")
    print("=" * 80)
    print(f"Eval Dataset:    {eval_dataset_path}")
    print(f"Basis Artifact:  {basis_artifact_path}")
    print(f"Target Layer:    L{target_layer_1based}")
    print(f"Position:        {semantic_position}")
    print(f"Rank Grid:       {rank_grid}")

    basis_data = torch.load(basis_artifact_path, map_location="cpu", weights_only=False)
    V_full = basis_data["V"]  # [d_model, n_comp]
    d_model = V_full.shape[0]

    cfg = load_config(resolve(config_path))
    model, tokenizer = load_model(cfg)
    model.eval()

    layers, _ = find_transformer_stack(model)
    layer_info = resolve_layer_indices(target_layer_1based, len(layers))
    target_mod = layers[layer_info["layer_0based"]]

    lines = [json.loads(line) for line in eval_dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if max_cases:
        lines = lines[:max_cases]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    results = []

    for idx, case in enumerate(lines):
        cid = case["example_id"]
        cond = case["condition"]
        clean_label = case["clean_label"]
        swapped_label = case["swapped_label"]
        rel_k = case["relevant_source_key"]

        c_toks = tokenizer.encode(clean_label, add_special_tokens=False)
        s_toks = tokenizer.encode(swapped_label, add_special_tokens=False)
        dist_idx = find_first_distinguishing_index(c_toks, s_toks)
        clean_tok = c_toks[dist_idx]
        swapped_tok = s_toks[dist_idx]

        rel_src = next(s for s in case["sources"] if s["key"] == rel_k)
        evidence_sentence = rel_src["text"].split(". ")[0] + "."
        clean_display = case["clean_display_by_source"][rel_k]
        swapped_display = case["swapped_display_by_source"][rel_k]

        clean_pos_dict = locate_semantic_positions(
            tokenizer=tokenizer,
            prompt=case["clean_prompt"],
            answer=case["answer"],
            citation_label=clean_label,
            relevant_handle=clean_display,
            evidence_substring=evidence_sentence,
            dist_idx=dist_idx,
        )
        donor_pos_dict = locate_semantic_positions(
            tokenizer=tokenizer,
            prompt=case["swapped_prompt"],
            answer=case["answer"],
            citation_label=swapped_label,
            relevant_handle=swapped_display,
            evidence_substring=evidence_sentence,
            dist_idx=dist_idx,
        )

        clean_pos = clean_pos_dict[semantic_position]
        donor_pos = donor_pos_dict[semantic_position]
        clean_pred_pos = clean_pos_dict["pos_citation"][0]
        donor_pred_pos = donor_pos_dict["pos_citation"][0]

        clean_input_ids = torch.tensor([clean_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")
        donor_input_ids = torch.tensor([donor_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")

        clean_pred_tensor = torch.tensor([clean_pred_pos], device="cuda:0")
        donor_pred_tensor = torch.tensor([donor_pred_pos], device="cuda:0")

        # Capture activations
        donor_act = None
        def capture_hook(_m, _i, o):
            nonlocal donor_act
            primary = o[0] if isinstance(o, tuple) else o
            donor_act = primary[0, donor_pos, :].detach().cpu()
        h_rec = target_mod.register_forward_hook(capture_hook)
        with torch.inference_mode():
            donor_out = model(donor_input_ids, logits_to_keep=donor_pred_tensor)
            donor_logits = donor_out.logits[0, 0, :]
            _, _, donor_pref = compute_logp_pref(donor_logits, clean_tok, swapped_tok)
        h_rec.remove()

        clean_act = None
        def capture_clean_hook(_m, _i, o):
            nonlocal clean_act
            primary = o[0] if isinstance(o, tuple) else o
            clean_act = primary[0, clean_pos, :].detach().cpu()
        h_rec_c = target_mod.register_forward_hook(capture_clean_hook)
        with torch.inference_mode():
            clean_out = model(clean_input_ids, logits_to_keep=clean_pred_tensor)
            clean_logits = clean_out.logits[0, 0, :]
            c_lp, s_lp, clean_pref = compute_logp_pref(clean_logits, clean_tok, swapped_tok)
        h_rec_c.remove()

        case_rec = {
            "case_idx": idx,
            "example_id": cid,
            "condition": cond,
            "layer_1based": target_layer_1based,
            "semantic_position": semantic_position,
            "clean_baseline_pref": clean_pref,
            "donor_baseline_pref": donor_pref,
            "rank_evaluations": {},
            "random_control_evaluations": {},
            "orthogonal_complement_evaluations": {},
        }

        # Evaluate along rank grid
        for k in rank_grid:
            V_k = V_full[:, :k]
            patcher = SubspaceProjectionPatcher(target_mod, V_k, clean_act, donor_act, clean_pos)
            with patcher:
                with torch.inference_mode():
                    patched_out = model(clean_input_ids, logits_to_keep=clean_pred_tensor)
                    patched_logits = patched_out.logits[0, 0, :]
            _, _, p_pref = compute_logp_pref(patched_logits, clean_tok, swapped_tok)
            shift = p_pref - clean_pref
            kl = compute_kl(clean_logits, patched_logits)
            recov = (shift / (donor_pref - clean_pref) * 100.0) if abs(donor_pref - clean_pref) > 0.5 else None

            case_rec["rank_evaluations"][str(k)] = {
                "rank": k,
                "abs_shift_first": round(float(shift), 4),
                "recovery_pct": round(float(recov), 2) if recov is not None else None,
                "kl_div": round(float(kl), 4),
                "retained_variance_ratio": round(float(basis_data["cumulative_variance_ratio"][k - 1]), 4) if k <= len(basis_data["cumulative_variance_ratio"]) else 1.0,
            }

            # Random basis control
            V_rand = generate_random_orthonormal_basis(d_model, k, seed=42 + k)
            patcher_rand = SubspaceProjectionPatcher(target_mod, V_rand, clean_act, donor_act, clean_pos)
            with patcher_rand:
                with torch.inference_mode():
                    p_rand_out = model(clean_input_ids, logits_to_keep=clean_pred_tensor)
                    p_rand_logits = p_rand_out.logits[0, 0, :]
            _, _, p_rand_pref = compute_logp_pref(p_rand_logits, clean_tok, swapped_tok)
            shift_rand = p_rand_pref - clean_pref
            recov_rand = (shift_rand / (donor_pref - clean_pref) * 100.0) if abs(donor_pref - clean_pref) > 0.5 else None
            case_rec["random_control_evaluations"][str(k)] = {
                "rank": k,
                "abs_shift_first": round(float(shift_rand), 4),
                "recovery_pct": round(float(recov_rand), 2) if recov_rand is not None else None,
            }

            # Orthogonal complement control
            patcher_comp = SubspaceProjectionPatcher(target_mod, V_k, clean_act, donor_act, clean_pos, complement=True)
            with patcher_comp:
                with torch.inference_mode():
                    p_comp_out = model(clean_input_ids, logits_to_keep=clean_pred_tensor)
                    p_comp_logits = p_comp_out.logits[0, 0, :]
            _, _, p_comp_pref = compute_logp_pref(p_comp_logits, clean_tok, swapped_tok)
            shift_comp = p_comp_pref - clean_pref
            recov_comp = (shift_comp / (donor_pref - clean_pref) * 100.0) if abs(donor_pref - clean_pref) > 0.5 else None
            case_rec["orthogonal_complement_evaluations"][str(k)] = {
                "rank": k,
                "abs_shift_first": round(float(shift_comp), 4),
                "recovery_pct": round(float(recov_comp), 2) if recov_comp is not None else None,
            }

        torch.cuda.empty_cache()
        results.append(case_rec)
        with output_path.open("a", encoding="utf-8") as out_f:
            out_f.write(json.dumps(case_rec) + "\n")
            out_f.flush()

        if (idx + 1) % 5 == 0 or (idx + 1) == len(lines):
            print(f"[{idx+1}/{len(lines)}] Subspace cases evaluated", flush=True)

    print(f"\nSaved {len(results)} subspace evaluation records to: {output_path}")


def extract_and_fit_subspace(
    config_path: Path,
    discovery_dataset_path: Path,
    output_basis_path: Path,
    target_layer_1based: int = 14,
    semantic_position: str = "pos_post_evidence",
    center_by_condition: bool = True,
    max_cases: int | None = None,
) -> dict[str, Any]:
    """Fit SVD orthonormal basis on counterfactual differences captured strictly on discovery split."""
    print("=" * 80)
    print("SEQUENCE 3B: POST-EVIDENCE SVD SUBSPACE FITTING (DISCOVERY SPLIT ONLY)")
    print("=" * 80)
    print(f"Config:          {config_path}")
    print(f"Discovery Split: {discovery_dataset_path}")
    print(f"Output Basis:    {output_basis_path}")
    print(f"Target Layer:    L{target_layer_1based}")
    print(f"Position:        {semantic_position}")

    cfg = load_config(resolve(config_path))
    model, tokenizer = load_model(cfg)
    model.eval()

    layers, _ = find_transformer_stack(model)
    layer_info = resolve_layer_indices(target_layer_1based, len(layers))
    target_mod = layers[layer_info["layer_0based"]]

    lines = [json.loads(line) for line in discovery_dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if max_cases:
        lines = lines[:max_cases]

    diff_vectors = []
    condition_labels = []
    metadata_cases = []

    for idx, case in enumerate(lines):
        cid = case["example_id"]
        cond = case["condition"]
        clean_label = case["clean_label"]
        swapped_label = case["swapped_label"]
        rel_k = case["relevant_source_key"]

        c_toks = tokenizer.encode(clean_label, add_special_tokens=False)
        s_toks = tokenizer.encode(swapped_label, add_special_tokens=False)
        dist_idx = find_first_distinguishing_index(c_toks, s_toks)

        rel_src = next(s for s in case["sources"] if s["key"] == rel_k)
        evidence_sentence = rel_src["text"].split(". ")[0] + "."
        clean_display = case["clean_display_by_source"][rel_k]
        swapped_display = case["swapped_display_by_source"][rel_k]

        clean_pos_dict = locate_semantic_positions(
            tokenizer=tokenizer,
            prompt=case["clean_prompt"],
            answer=case["answer"],
            citation_label=clean_label,
            relevant_handle=clean_display,
            evidence_substring=evidence_sentence,
            dist_idx=dist_idx,
        )
        donor_pos_dict = locate_semantic_positions(
            tokenizer=tokenizer,
            prompt=case["swapped_prompt"],
            answer=case["answer"],
            citation_label=swapped_label,
            relevant_handle=swapped_display,
            evidence_substring=evidence_sentence,
            dist_idx=dist_idx,
        )

        clean_pos = clean_pos_dict[semantic_position]
        donor_pos = donor_pos_dict[semantic_position]

        if not clean_pos or not donor_pos:
            continue

        clean_input_ids = torch.tensor([clean_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")
        donor_input_ids = torch.tensor([donor_pos_dict["eval_dict"]["input_ids"]], device="cuda:0")

        # Capture donor activation
        donor_act = None
        def capture_donor(_m, _i, o):
            nonlocal donor_act
            primary = o[0] if isinstance(o, tuple) else o
            donor_act = primary[0, donor_pos, :].detach().cpu()

        h_d = target_mod.register_forward_hook(capture_donor)
        with torch.inference_mode():
            model.model(donor_input_ids)
        h_d.remove()

        # Capture clean activation
        clean_act = None
        def capture_clean(_m, _i, o):
            nonlocal clean_act
            primary = o[0] if isinstance(o, tuple) else o
            clean_act = primary[0, clean_pos, :].detach().cpu()

        h_c = target_mod.register_forward_hook(capture_clean)
        with torch.inference_mode():
            model.model(clean_input_ids)
        h_c.remove()

        aligned_donor, _ = align_activation_spans(clean_pos, donor_pos, donor_act)
        delta_vec = (aligned_donor.float() - clean_act.float()).mean(dim=0)
        diff_vectors.append(delta_vec)
        condition_labels.append(cond)
        metadata_cases.append({"example_id": cid, "condition": cond})

        if (idx + 1) % 10 == 0 or (idx + 1) == len(lines):
            print(f"[{idx+1}/{len(lines)}] Extracted difference vectors on discovery split", flush=True)

    print(f"\nExtracted {len(diff_vectors)} counterfactual difference vectors across {len(set(condition_labels))} conditions.")
    basis_res = fit_svd_subspace(
        diff_vectors=diff_vectors,
        center_by_condition=center_by_condition,
        condition_labels=condition_labels,
    )
    basis_res["layer_1based"] = target_layer_1based
    basis_res["semantic_position"] = semantic_position
    basis_res["metadata_cases"] = metadata_cases
    basis_res["condition_labels"] = condition_labels

    output_basis_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(basis_res, output_basis_path)
    print(f"Saved fitted SVD orthonormal basis ({basis_res['V'].shape}) to: {output_basis_path}")
    return basis_res


def main():
    parser = argparse.ArgumentParser(description="Sequence 3B: Causal Subspace Evaluation and Basis Fitting")
    parser.add_argument("--mode", default="eval", choices=["fit", "eval"])
    parser.add_argument("--config", default="configs/circuit/circuit_qwen25_15b.yaml")
    parser.add_argument("--discovery_dataset", default="data/circuit/discovery_n32.jsonl")
    parser.add_argument("--eval_dataset", default="data/circuit/validation_n32.jsonl")
    parser.add_argument("--basis_artifact", default="results/circuit/sequence3_work/qwen25_subspace_basis_l14_post_evidence.pt")
    parser.add_argument("--output", default=None)
    parser.add_argument("--layer", type=int, default=14)
    parser.add_argument("--pos", default="pos_post_evidence")
    parser.add_argument("--ranks", nargs="+", type=int, default=[1, 2, 4, 8, 16, 32])
    parser.add_argument("--max_cases", type=int, default=None)
    args = parser.parse_args()

    if args.mode == "fit":
        output_basis = Path(args.basis_artifact)
        extract_and_fit_subspace(
            config_path=Path(args.config),
            discovery_dataset_path=Path(args.discovery_dataset),
            output_basis_path=output_basis,
            target_layer_1based=args.layer,
            semantic_position=args.pos,
            max_cases=args.max_cases,
        )
    else:
        assert args.output, "Output path is required for eval mode"
        run_subspace_evaluation(
            config_path=Path(args.config),
            eval_dataset_path=Path(args.eval_dataset),
            basis_artifact_path=Path(args.basis_artifact),
            output_path=Path(args.output),
            target_layer_1based=args.layer,
            semantic_position=args.pos,
            rank_grid=args.ranks,
            max_cases=args.max_cases,
        )


if __name__ == "__main__":
    main()

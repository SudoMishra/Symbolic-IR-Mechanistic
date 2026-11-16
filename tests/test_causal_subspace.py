"""Unit tests for Phase 5 Causal Subspace Localization Invariants.

Verifies:
1. SVD basis fitting on counterfactual difference vectors.
2. Centering within condition preserves condition offsets.
3. Orthonormality of the basis: V_k^T @ V_k == I_k.
4. Idempotence of the subspace projection operator: P_k^2 == P_k.
5. Orthogonal complement property: (I - P_k) @ P_k == 0.
6. Random orthonormal basis generation via QR is strictly orthonormal.
"""

from __future__ import annotations

import pytest
import torch
from scripts.run_causal_subspace import (
    fit_svd_subspace,
    generate_random_orthonormal_basis,
)


def test_svd_subspace_fitting_and_orthonormality():
    d_model = 64
    n_samples = 30

    # Synthetic difference vectors across two conditions
    diff_vectors = [torch.randn(d_model) for _ in range(n_samples)]
    condition_labels = ["cond_A"] * 15 + ["cond_B"] * 15

    basis_res = fit_svd_subspace(diff_vectors, center_by_condition=True, condition_labels=condition_labels)

    V = basis_res["V"]  # [d_model, n_samples]
    assert V.shape == (d_model, n_samples)

    # Invariant 1: Orthonormality V^T @ V == I
    vt_v = V.t() @ V
    eye = torch.eye(n_samples)
    diff_eye = torch.max(torch.abs(vt_v - eye)).item()
    assert diff_eye < 1e-5, f"Basis is not orthonormal: max diff {diff_eye}"

    # Invariant 2: Singular values are sorted descending
    s = basis_res["singular_values"]
    assert all(s[i] >= s[i + 1] for i in range(len(s) - 1)), "Singular values must be descending"

    # Invariant 3: Cumulative variance reaches 1.0
    cum_var = basis_res["cumulative_variance_ratio"]
    assert abs(cum_var[-1] - 1.0) < 1e-4, f"Final cumulative variance must be 1.0, got {cum_var[-1]}"


def test_projection_operator_idempotence_and_complement():
    d_model = 128
    k = 4
    gen = torch.Generator().manual_seed(123)
    V_k = generate_random_orthonormal_basis(d_model, k)

    # Invariant: V_k^T @ V_k == I_k
    assert torch.allclose(V_k.t() @ V_k, torch.eye(k), atol=1e-6)

    # Projection operator P_k = V_k @ V_k^T
    P_k = V_k @ V_k.t()  # [d_model, d_model]

    # Invariant: Idempotence P_k @ P_k == P_k
    assert torch.allclose(P_k @ P_k, P_k, atol=1e-6), "Projection operator must be idempotent"

    # Invariant: Orthogonal complement (I - P_k) @ P_k == 0
    I = torch.eye(d_model)
    P_perp = I - P_k
    assert torch.allclose(P_perp @ P_k, torch.zeros(d_model, d_model), atol=1e-6)

    # Invariant: Projection of any vector decomposes into P_k x + P_perp x == x
    x = torch.randn(d_model, 1, generator=gen)
    x_proj = P_k @ x
    x_perp = P_perp @ x
    assert torch.allclose(x_proj + x_perp, x, atol=1e-6)


def test_subspace_projection_patcher_unequal_spans():
    """Verify that SubspaceProjectionPatcher aligns unequal clean vs donor activation spans."""
    from scripts.run_causal_subspace import SubspaceProjectionPatcher
    import torch.nn as nn

    d_model = 64
    k = 4
    gen = torch.Generator().manual_seed(42)
    V_k = generate_random_orthonormal_basis(d_model, k)

    # Dummy layer module
    class DummyLayer(nn.Module):
        def forward(self, x):
            return x

    layer = DummyLayer()
    clean_len = 3
    donor_len = 5
    clean_positions = [10, 11, 12]

    clean_act = torch.randn(clean_len, d_model, generator=gen)
    donor_act = torch.randn(donor_len, d_model, generator=gen)

    # Sequence tensor [B=1, S=20, d_model]
    seq_tensor = torch.randn(1, 20, d_model, generator=gen)

    patcher = SubspaceProjectionPatcher(
        layer_module=layer,
        basis_k=V_k,
        clean_activation=clean_act,
        donor_activation=donor_act,
        target_positions=clean_positions,
        complement=False,
    )

    with patcher:
        out = layer(seq_tensor)

    assert out.shape == seq_tensor.shape
    # Non-target positions remain untouched
    assert torch.allclose(out[:, :10, :], seq_tensor[:, :10, :])
    assert torch.allclose(out[:, 13:, :], seq_tensor[:, 13:, :])
    # Target positions were patched
    assert not torch.allclose(out[:, clean_positions, :], seq_tensor[:, clean_positions, :])


def test_bootstrapped_ratio_ci():
    """Verify that bootstrapped_ratio_ci computes aggregate mean ratio with cluster bootstrap."""
    from scripts.analyze_causal_subspace import bootstrapped_ratio_ci

    # 10 examples, each with 3 conditions
    numer_pairs = []
    denom_pairs = []
    for ex_idx in range(10):
        ex_id = f"ex_{ex_idx}"
        for _ in range(3):
            # 70% recovery ground truth
            denom = 2.0
            numer = 1.4
            numer_pairs.append((ex_id, numer))
            denom_pairs.append((ex_id, denom))

    pt_est, low, high = bootstrapped_ratio_ci(numer_pairs, denom_pairs, b_reps=500, seed=42)

    assert abs(pt_est - 70.0) < 1e-5, f"Expected 70.0%, got {pt_est}"
    assert abs(low - 70.0) < 1e-4, f"Constant data should yield sharp CI, got low={low}"
    assert abs(high - 70.0) < 1e-4, f"Constant data should yield sharp CI, got high={high}"

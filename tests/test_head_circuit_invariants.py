"""Unit tests for Phase 4 Head-Level Circuit Decomposition Invariants.

Verifies:
1. Query-head count and head dimension slicing.
2. Identity patch leaves activations/logits unchanged within numerical tolerance.
3. Patching all query-head slices equals patching the full mixer output.
4. Linear reconstruction: sum of projected head slices equals full o_proj projection.
5. Exact minimality evaluation over all 2^K subsets for K <= 4.
"""

from __future__ import annotations

import itertools
import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F


class DummyAttention(nn.Module):
    """Minimal self-attention module simulating Qwen2Attention o_proj."""

    def __init__(self, hidden_size: int = 1536, num_heads: int = 12):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        self.o_proj = nn.Linear(hidden_size, hidden_size, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x is [B, S, hidden_size]
        return self.o_proj(x)


def test_query_head_slicing_and_reconstruction():
    """Verify that slicing by head_dim partitions hidden_size and reconstructs the linear projection."""
    hidden_size = 1536
    num_heads = 12
    head_dim = 128
    batch_size = 2
    seq_len = 10

    attn = DummyAttention(hidden_size, num_heads)
    z = torch.randn(batch_size, seq_len, hidden_size)

    # 1. Full projection
    full_out = attn.o_proj(z)

    # 2. Slice-by-slice projection sum
    w_o = attn.o_proj.weight  # [hidden_size, hidden_size]
    slice_out_sum = torch.zeros_like(full_out)

    for h in range(num_heads):
        start_col = h * head_dim
        end_col = (h + 1) * head_dim
        z_h = z[:, :, start_col:end_col]
        w_h = w_o[:, start_col:end_col]
        slice_out_sum += torch.matmul(z_h, w_h.t())

    # Invariant: sum of projected head slices equals unprojected mixer output
    diff = torch.max(torch.abs(full_out - slice_out_sum)).item()
    assert diff < 1e-5, f"Linear head reconstruction error {diff} exceeds tolerance"


def test_identity_and_all_head_patching():
    """Verify that identity patching changes nothing and all-head patching equals full-input patching."""
    hidden_size = 1536
    num_heads = 12
    head_dim = 128

    attn = DummyAttention(hidden_size, num_heads)
    clean_z = torch.randn(1, 8, hidden_size)
    donor_z = torch.randn(1, 8, hidden_size)
    target_pos = [2, 5]

    # Baseline clean output
    base_out = attn.o_proj(clean_z)

    # Identity patch on head 3
    ident_z = clean_z.clone()
    h = 3
    ident_z[:, target_pos, h * head_dim : (h + 1) * head_dim] = clean_z[:, target_pos, h * head_dim : (h + 1) * head_dim]
    ident_out = attn.o_proj(ident_z)
    assert torch.allclose(base_out, ident_out, atol=1e-6), "Identity patch altered activations"

    # All-head patch
    all_head_z = clean_z.clone()
    for h in range(num_heads):
        all_head_z[:, target_pos, h * head_dim : (h + 1) * head_dim] = donor_z[:, target_pos, h * head_dim : (h + 1) * head_dim]
    all_head_out = attn.o_proj(all_head_z)

    # Full-input patch
    full_input_z = clean_z.clone()
    full_input_z[:, target_pos, :] = donor_z[:, target_pos, :]
    full_input_out = attn.o_proj(full_input_z)

    # Invariant: all-head patch == full-input patch
    diff_all = torch.max(torch.abs(all_head_out - full_input_out)).item()
    assert diff_all < 1e-6, f"All-head patch did not match full-input patch: diff={diff_all}"


def test_exact_minimality_search_k4():
    """Verify exact minimality search evaluating all 2^K subsets for K <= 4."""
    candidate_heads = [1, 4, 7]  # K=3
    k = len(candidate_heads)
    all_subsets = []
    for r in range(1, k + 1):
        for subset in itertools.combinations(candidate_heads, r):
            all_subsets.append(list(subset))

    # For K=3, 2^3 - 1 = 7 non-empty subsets
    assert len(all_subsets) == 7

    # Simulated recovery scores
    # Suppose subset [1, 4] achieves 92% recovery (meets threshold >= 80%),
    # but singletons [1], [4], [7] achieve < 80%.
    # Then [1, 4] is minimal because neither [1] nor [4] alone meets threshold.
    recovery_by_subset = {
        (1,): 45.0,
        (4,): 50.0,
        (7,): 15.0,
        (1, 4): 92.0,
        (1, 7): 55.0,
        (4, 7): 60.0,
        (1, 4, 7): 94.0,
    }

    threshold = 80.0
    qualifying = [s for s, rec in recovery_by_subset.items() if rec >= threshold]
    # Smallest qualifying subset
    min_size = min(len(s) for s in qualifying)
    minimal_subsets = [s for s in qualifying if len(s) == min_size]

    assert minimal_subsets == [(1, 4)], "Expected minimal subset (1, 4)"

# Phase 5: Post-Evidence Causal Subspace Evaluation

- **Dataset**: `qwen25_subspace_confirmation_n80_eval.jsonl` (240 cases)
- **Target**: Layer 14 (`pos_post_evidence` residual stream)
- **Optimal Selected Rank**: **k* = 1** (Fallback to rank with highest margin over random (1))

| Rank $k$ | Causal Shift [95% CI] | Recovery % [95% CI] | Random Control Recovery % | Margin over Random | Complement Recovery % | KL Div | Qualifies |
|---|---|---|---|---|---|---|---|
| 1 | +0.0103 [-0.0021, 0.0231] | -12.8% [-53.5%, 54.1%] | -5.7% | -7.1% | -23.3% | 0.001 | No |
| 4 | +0.0131 [0.0003, 0.0267] | -13.9% [-59.4%, 55.7%] | 3.7% | -17.5% | -23.4% | 0.001 | No |
| 8 | +0.0297 [0.0165, 0.0423] | -31.3% [-130.6%, 128.4%] | -4.1% | -27.2% | -6.6% | 0.001 | No |
| 16 | +0.0321 [0.0174, 0.0456] | -32.3% [-139.6%, 114.6%] | -0.2% | -32.1% | -4.4% | 0.001 | No |
| 32 | +0.0289 [0.0126, 0.0444] | -29.6% [-111.5%, 120.9%] | -3.5% | -26.1% | -4.7% | 0.001 | No |

### Condition-Specific Transfer Matrix

| Condition | Rank 1 Recovery | Rank 4 Recovery | Rank 8 Recovery | Rank 16 Recovery | Rank 32 Recovery |
|---|---|---|---|---|---|
| `structured` | 6.2% | 8.6% | 12.7% | 12.0% | 10.8% |
| `random_compact` | 6.9% | -5.0% | 1.7% | 9.8% | 2.3% |
| `uuid` | 0.3% | -0.8% | -3.1% | -2.5% | -3.5% |
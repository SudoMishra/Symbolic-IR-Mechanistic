# Phase 5: Post-Evidence Causal Subspace Evaluation

- **Dataset**: `qwen25_subspace_validation_n32_eval.jsonl` (96 cases)
- **Target**: Layer 14 (`pos_post_evidence` residual stream)
- **Optimal Selected Rank**: **k* = 1** (Fallback to rank with highest margin over random (1))

| Rank $k$ | Causal Shift [95% CI] | Recovery % [95% CI] | Random Control Recovery % | Margin over Random | Complement Recovery % | KL Div | Qualifies |
|---|---|---|---|---|---|---|---|
| 1 | +0.0120 [-0.0098, 0.0319] | -2.1% [-27.9%, 18.9%] | -2.4% | +0.3% | -2.2% | 0.001 | No |
| 2 | +0.0149 [-0.0128, 0.0439] | -2.0% [-24.6%, 21.8%] | -1.4% | -0.6% | -3.5% | 0.002 | No |
| 4 | +0.0129 [-0.0121, 0.0377] | -1.9% [-27.7%, 21.3%] | -1.6% | -0.3% | -2.0% | 0.002 | No |
| 8 | +0.0249 [0.0028, 0.0481] | -4.0% [-48.8%, 40.7%] | -2.4% | -1.5% | -2.5% | 0.002 | No |
| 16 | +0.0208 [0.0004, 0.0445] | -2.7% [-31.4%, 25.5%] | -1.6% | -1.1% | -2.3% | 0.002 | No |
| 32 | +0.0272 [0.0044, 0.0480] | -3.5% [-36.9%, 31.8%] | -1.0% | -2.5% | -2.8% | 0.002 | No |

### Condition-Specific Transfer Matrix

| Condition | Rank 1 Recovery | Rank 4 Recovery | Rank 8 Recovery | Rank 16 Recovery | Rank 32 Recovery |
|---|---|---|---|---|---|
| `structured` | 27.7% | 19.6% | 34.2% | 24.9% | 21.2% |
| `random_compact` | -0.4% | -1.7% | 0.1% | -0.7% | -1.6% |
| `uuid` | -0.4% | 0.1% | -3.0% | -1.4% | -2.4% |
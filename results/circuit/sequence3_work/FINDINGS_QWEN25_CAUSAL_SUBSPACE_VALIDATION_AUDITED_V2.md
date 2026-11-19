# Phase 5: Post-Evidence Causal Subspace Evaluation (Validation Audited)

- **Dataset**: `qwen25_subspace_validation_n32_eval.jsonl` (96 cases)
- **Target**: Layer 14 (`pos_post_evidence` residual stream)
- **Selection Outcome**: `no_rank_qualified` (optimal_rank: `None`)
- **Status Note**: No rank qualified: 0/6 ranks met recovery >= 70.0% and margin_over_random >= 30.0%
- **Exploratory Best Margin Rank**: Rank 1 (+0.26% margin)

| Rank $k$ | Eligible Rows | Causal Shift [95% CI] | Numerator Mean | Denominator Mean | Recovery % [95% CI] | Ratio Status | Random Control Shift | Paired Shift Diff [95% CI] | Margin over Random % [95% CI] | Complement Recovery % | Qualifies |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 81/96 | +0.0120 [-0.0084, 0.0303] | +0.0151 | -0.7126 | -2.1% [unidentifiable] | `not_identifiable_under_policy` | +0.0122 | -0.0002 [-0.0174, 0.0180] | +0.3% [unidentifiable] | -2.2% | No |
| 2 | 81/96 | +0.0149 [-0.0112, 0.0407] | +0.0142 | -0.7126 | -2.0% [unidentifiable] | `not_identifiable_under_policy` | +0.0110 | +0.0039 [-0.0208, 0.0287] | -0.6% [unidentifiable] | -3.5% | No |
| 4 | 81/96 | +0.0129 [-0.0096, 0.0366] | +0.0132 | -0.7126 | -1.9% [unidentifiable] | `not_identifiable_under_policy` | +0.0076 | +0.0054 [-0.0123, 0.0262] | -0.3% [unidentifiable] | -2.0% | No |
| 8 | 81/96 | +0.0249 [0.0030, 0.0459] | +0.0282 | -0.7126 | -4.0% [unidentifiable] | `not_identifiable_under_policy` | +0.0116 | +0.0133 [-0.0075, 0.0343] | -1.5% [unidentifiable] | -2.5% | No |
| 16 | 81/96 | +0.0208 [-0.0024, 0.0439] | +0.0194 | -0.7126 | -2.7% [unidentifiable] | `not_identifiable_under_policy` | +0.0115 | +0.0093 [-0.0080, 0.0260] | -1.1% [unidentifiable] | -2.3% | No |
| 32 | 81/96 | +0.0272 [0.0047, 0.0486] | +0.0249 | -0.7126 | -3.5% [unidentifiable] | `not_identifiable_under_policy` | +0.0072 | +0.0200 [0.0027, 0.0383] | -2.5% [unidentifiable] | -2.8% | No |

### Condition-Specific Transfer Matrix

| Condition | Eligible Rows | Rank 1 Recovery | Rank 2 Recovery | Rank 4 Recovery | Rank 8 Recovery | Rank 16 Recovery | Rank 32 Recovery |
|---|---|---|---|---|---|---|---|
| `random_compact` | 28/32 | -0.4% | -2.0% | -1.7% | 0.1% | -0.7% | -1.6% |
| `structured` | 24/32 | N/A | N/A | N/A | N/A | N/A | N/A |
| `uuid` | 29/32 | -0.4% | -0.8% | 0.1% | -3.0% | -1.4% | -2.4% |
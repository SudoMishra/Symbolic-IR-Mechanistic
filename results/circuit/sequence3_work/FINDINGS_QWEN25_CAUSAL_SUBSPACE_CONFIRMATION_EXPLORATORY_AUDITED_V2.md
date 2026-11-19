# Phase 5: Post-Evidence Causal Subspace Evaluation (Exploratory Confirmation Audited)

- **Dataset**: `qwen25_subspace_confirmation_n80_eval.jsonl` (240 cases)
- **Target**: Layer 14 (`pos_post_evidence` residual stream)
- **Selection Outcome**: `exploratory_evaluation_no_selection` (optimal_rank: `None`)
- **Status Note**: EXPLORATORY EVALUATION: No rank selection permitted; all registered qualification flags are false.
- **Exploratory Best Margin Rank**: None (All candidate ranks have undefined or unidentifiable margin over random under stated policy.)

> [!IMPORTANT]
> **EXPLORATORY PROTOCOL NOTICE**: This confirmation evaluation is exploratory. Following the preregistered protocol, because no rank met the qualification thresholds on validation, no rank was validated or frozen. Multiple ranks were evaluated. All qualification flags are false, and confirmation data are fully consumed.

| Rank $k$ | Eligible Rows | Causal Shift [95% CI] | Numerator Mean | Denominator Mean | Recovery % [95% CI] | Ratio Status | Random Control Shift | Paired Shift Diff [95% CI] | Margin over Random % [95% CI] | Complement Recovery % | Qualifies |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 195/240 | +0.0103 [-0.0024, 0.0229] | +0.0123 | -0.0955 | N/A | `denominator_below_aggregate_guard` | +0.0039 | +0.0065 [-0.0051, 0.0184] | N/A | N/A | No |
| 4 | 195/240 | +0.0131 [0.0018, 0.0266] | +0.0132 | -0.0955 | N/A | `denominator_below_aggregate_guard` | -0.0057 | +0.0188 [0.0071, 0.0336] | N/A | N/A | No |
| 8 | 195/240 | +0.0297 [0.0170, 0.0430] | +0.0299 | -0.0955 | N/A | `denominator_below_aggregate_guard` | +0.0015 | +0.0282 [0.0148, 0.0419] | N/A | N/A | No |
| 16 | 195/240 | +0.0321 [0.0188, 0.0486] | +0.0309 | -0.0955 | N/A | `denominator_below_aggregate_guard` | -0.0029 | +0.0350 [0.0196, 0.0510] | N/A | N/A | No |
| 32 | 195/240 | +0.0289 [0.0136, 0.0464] | +0.0283 | -0.0955 | N/A | `denominator_below_aggregate_guard` | +0.0036 | +0.0253 [0.0109, 0.0402] | N/A | N/A | No |

### Condition-Specific Transfer Matrix

| Condition | Eligible Rows | Rank 1 Recovery | Rank 4 Recovery | Rank 8 Recovery | Rank 16 Recovery | Rank 32 Recovery |
|---|---|---|---|---|---|---|
| `random_compact` | 64/80 | N/A | N/A | N/A | N/A | N/A |
| `structured` | 65/80 | N/A | N/A | N/A | N/A | N/A |
| `uuid` | 66/80 | 0.3% | -0.8% | -3.1% | -2.5% | -3.5% |
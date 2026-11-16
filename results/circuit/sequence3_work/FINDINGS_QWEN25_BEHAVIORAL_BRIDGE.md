# Phase 6: Behavioral Bridge Free Generation Findings

- **Dataset**: `qwen25_behavioral_bridge_validation.jsonl` (96 cases)
- **Target Intervention**: Layer 14 `pos_post_evidence` Subspace Projection (Rank 8)

| Evaluation Condition | Answer EM [95% CI] | Cites Target [95% CI] | Precision [95% CI] | Recall [95% CI] | Selective Dissociation [95% CI] | Strict Syntax [95% CI] |
|---|---|---|---|---|---|---|
| **Clean Prompt Baseline** | 40.6% [26.0%, 57.3%] | 11.5% [4.2%, 19.8%] | 8.3% [2.6%, 14.6%] | 11.5% [4.2%, 19.8%] | N/A | 64.6% [53.1%, 74.0%] |
| **Swapped Prompt Baseline** | 39.6% [25.0%, 55.2%] | 25.0% [14.6%, 35.4%] | 16.1% [8.8%, 24.0%] | 25.0% [14.6%, 35.4%] | N/A | 55.2% [42.7%, 67.7%] |
| **Subspace Patched (L14 Rank 8)** | 40.6% [26.0%, 57.3%] | 11.5% [4.2%, 19.8%] | 7.9% [2.6%, 14.6%] | 12.5% [4.2%, 21.9%] | 8.3% [2.1%, 16.7%] | 63.5% [51.0%, 74.0%] |

### Error Taxonomy Breakdown

| Evaluation Condition | Error Free | Counterfactual Cited | Omitted Citation | Wrong Source | Spurious Citation | Answer Incorrect | Both Incorrect |
|---|---|---|---|---|---|---|---|
| `clean_baseline` | 0 | 8 | 0 | 31 | 0 | 9 | 48 |
| `swapped_baseline` | 4 | 6 | 1 | 27 | 0 | 19 | 39 |
| `subspace_projection` | 0 | 8 | 0 | 31 | 0 | 10 | 47 |
# Phase 6: Behavioral Bridge Free Generation Causal Analysis (Audited)

- **Dataset**: `qwen25_behavioral_bridge_validation.jsonl` (96/96 cases evaluated across 32 clusters; 0 missing)
- **Target Intervention**: Layer 14 `pos_post_evidence` Subspace Projection (Rank 8)
- **Terminal Behavioral Status**: `paired_behavioral_effect: None`
- **Scientific Conclusion**: Null behavioral intervention effect: Subspace projection (L14 Rank 8) produced no citation redirection under free generation. Patched-minus-clean paired difference for counterfactual citations was 0.00% [0.00%, 0.00%], with zero 0->1 transitions. The 11.46% rate of counterfactual citations (and 8.33% joint correct-answer with counterfactual-citation prevalence) observed in intervened outputs reflects pre-existing baseline generation errors present in the clean baseline (11.46% and 8.33%, respectively) without causal effect from the subspace intervention.

### Paired Causal Intervention Effects (Patched Minus Clean)

| Metric | Clean Prevalence [95% CI] | Patched Prevalence [95% CI] | Paired Difference [95% CI] | Transitions (0->0, 0->1, 1->0, 1->1) | Causal Redirection |
|---|---|---|---|---|---|
| `answer_em` | 40.6% [25.0%, 58.3%] | 40.6% [25.0%, 58.3%] | +0.0% [0.0%, 0.0%] | 57, 0, 0, 39 | **None (0.0%)** |
| `cites_gold` | 11.5% [4.2%, 19.8%] | 12.5% [4.2%, 21.9%] | +1.0% [-2.1%, 4.2%] | 83, 2, 1, 10 | +1.0% |
| `cites_counterfactual` | 11.5% [4.2%, 20.8%] | 11.5% [4.2%, 20.8%] | +0.0% [0.0%, 0.0%] | 85, 0, 0, 11 | **None (0.0%)** |
| `citation_precision` | 8.3% [2.6%, 14.6%] | 7.9% [2.4%, 14.6%] | -0.4% [-3.0%, 1.6%] | N/A (continuous metric) | -0.4% |
| `citation_recall` | 11.5% [4.2%, 19.8%] | 12.5% [4.2%, 21.9%] | +1.0% [-2.1%, 4.2%] | N/A (continuous metric) | +1.0% |
| `strict_syntax` | 64.6% [53.1%, 75.0%] | 63.5% [51.0%, 75.0%] | -1.0% [-3.1%, 0.0%] | 34, 0, 1, 61 | -1.0% |
| `answer_correct_with_counterfactual_citation` | 8.3% [2.1%, 16.7%] | 8.3% [2.1%, 16.7%] | +0.0% [0.0%, 0.0%] | 88, 0, 0, 8 | **None (0.0%)** |

### Condition-Specific Format Breakdown

| Format | Cases | Clean Answer EM | Patched Answer EM | Paired EM Diff | Clean CF Cites | Patched CF Cites | Paired CF Cites Diff | CF Transitions (0->1) |
|---|---|---|---|---|---|---|---|---|
| `random_compact` | 32 | 37.5% | 37.5% | +0.0% | 15.6% | 15.6% | +0.0% | 0 |
| `structured` | 32 | 37.5% | 37.5% | +0.0% | 6.2% | 6.2% | +0.0% | 0 |
| `uuid` | 32 | 46.9% | 46.9% | +0.0% | 12.5% | 12.5% | +0.0% | 0 |

### Error Taxonomy Across Conditions

| Condition | Counterfactual Cited | Wrong Source | Answer Incorrect | Both Incorrect | Omitted Citation |
|---|---|---|---|---|---|
| `clean_baseline` | 8 | 31 | 9 | 48 | 0 |
| `swapped_baseline` | 6 | 27 | 19 | 39 | 1 |
| `subspace_projection` | 8 | 31 | 10 | 47 | 0 |
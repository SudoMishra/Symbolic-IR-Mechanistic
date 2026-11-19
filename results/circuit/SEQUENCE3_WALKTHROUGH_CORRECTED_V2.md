# Sequence 3 Reproducibility Walkthrough (Audited & Corrected V2)

## 1. Executive Summary & Terminal Scientific Outcome
- **Terminal Registered Scientific Outcome**: `valid_negative_result`
- **Exploratory Observational Status**: `exploratory_protocol_deviation`
- **Model**: Qwen 2.5 1.5B Instruct (`Qwen/Qwen2.5-1.5B-Instruct`)
- **Key Audited Findings**:
  1. **Sequence 2R (Positive Controls & Semantic Repair)**: Evaluating distinguishing token logits at $d-1$ confirmed that the whole attention mixer at Layer 24 `pos_citation` has a statistical null causal effect on distinguishing citation targets ($+0.001$ $[-0.147, +0.179]$). The residual stream carries strong handle-identity representation at `pos_source_label` ($+2.125$ $[1.733, 2.552]$) and a modest binding effect at Layer 14 `pos_post_evidence` ($+0.042$ $[0.018, 0.064]$ under label swap).
  2. **Sequence 3A (Attention Head Decomposition)**: Terminated cleanly as a **preregistered scientific null**. Whole-mixer positive control was null; head screening was disabled per protocol without post-hoc search across extra layers.
  3. **Sequence 3B (Post-Evidence Residual Subspace Validation)**: Terminated as **no rank qualified** on the validation cohort ($N=32$, 96 cases). No rank achieved the registered thresholds ($\ge 70\%$ recovery, $\ge 30\%$ margin over random).
  4. **Phase 6 (Behavioral Bridge Free Generation)**: Post-evidence subspace intervention (L14 Rank 8) produced **zero paired behavioral effect** ($0.00\%$ $[0.00\%, 0.00\%]$ across answer EM, counterfactual citations, and selective dissociation; zero $0 \to 1$ transitions). Baseline clean generation already exhibited counterfactual citation in $11.46\%$ of cases, and joint answer correctness with counterfactual citation in $8.33\%$ of cases.
  5. **Phase 7 (Confirmation Cohort)**: Reclassified as **exploratory analysis** due to multi-rank evaluation ($k \in \{1, 4, 8, 16, 32\}$) and absence of a validated frozen rank. The confirmation cohort ($N=80$, 240 cases) is consumed.
  6. **Denominator Sensitivity Policy (Amendment 002)**: On validation, aggregate denominator mean was $-0.7126$; resamples were unstable (`not_identifiable_under_policy`). On confirmation, the aggregate denominator mean across the 195 eligible cases was **$-0.0955$** (calculated from raw rows, not $-0.7042$), failing the $0.5$ aggregate guard and yielding undefined ratios.
  7. **Narrow Scope of Negative Result**: The tested basis/rank/positions failed the selection criteria; this does not warrant a general claim that binding subspaces or citation circuits do not exist in transformers.

---

## 2. Provenance & Artifact Hashes

All protected artifacts have been verified byte-for-byte against `data/circuit/dataset_manifest.json`:

| Artifact | Relative Path | Verified SHA-256 | Status |
|---|---|---|---|
| Discovery Cohort | `data/circuit/discovery_n32.jsonl` | `9112c31c27c6ed5d55d8a0d12b9a8399b38267ef5cafa710d27e5e0145e2f41e` | LOCKED |
| Validation Cohort | `data/circuit/validation_n32.jsonl` | `36435991721f830477393d53c56bcb6cced8c04c327b6ac2d54dd613acacd9d7` | LOCKED |
| Confirmation Cohort | `data/circuit/confirmation_n80.jsonl` | `3f5c66fa16dba4c88f40bd938a5ea237c554d9e8caff8a78838b8954437d54bd` | CONSUMED |
| Historical Preregistration | `results/circuit/circuit_preregistration.json` | `12363b12ad0d1d0acf28d9ed3d95478624f5515cd8f371dca95f839cc454f8af` | LOCKED |
| Sequence 3 Preregistration | `results/circuit/sequence3_preregistration.json` | `23f532fed2d7c88a868a124f6259ce2f5c9a50ca2cea31e70e4254298bc178fd` | LOCKED |
| Preregistration Amendment 001 | `results/circuit/sequence3_preregistration_amendment_001.json` | `884311687e33e0c507addff657b645cbf0bf82c92853f543d69497498517b3f3` | LOCKED |
| Preregistration Amendment 002 | `results/circuit/sequence3_preregistration_amendment_002.json` | `57b54b9aacdea7283583a3ee6b41b3d41208d267f20ff8f8803ccf5ce8d6b621` | LOCKED |

### Raw Sequence 3 Result Artifacts (Immutable):
- Discovery Repaired: `results/circuit/sequence3_work/qwen25_computation_vs_transport_discovery_n32_repaired.jsonl` (`37cf2a49e22ba90299f8672791c5156ca1f4c5e7d1ed499cef208a7afd84ac5e`, 96 rows)
- Subspace Validation: `results/circuit/sequence3_work/qwen25_subspace_validation_n32_eval.jsonl` (`f473107e7ac50242c1326b04ce2441e2b8698c1396277d26f5a0ba6904666d60`, 96 rows)
- Subspace Confirmation: `results/circuit/sequence3_work/qwen25_subspace_confirmation_n80_eval.jsonl` (`ffa6bf6beb9b17147461466404d61898a8ae31908bd171b6ee86fa11c6bb8088`, 240 rows)
- Behavioral Bridge: `results/circuit/sequence3_work/qwen25_behavioral_bridge_validation.jsonl` (`0e1159f9f23d54cbb23b3ef8acdbf785d6b92c8c0b78e5c0620a7345c5c492f6`, 96 rows)
- Fitted Basis: `results/circuit/sequence3_work/qwen25_subspace_basis_l14_post_evidence.pt` (`dba5e925730e90fde8cfcb90cb4244ae6207ebc097f7469179e2c8d64ccb362b`)

---

## 3. Audited V2 Reproduction Commands

### Step 1: Run Full Test Suite
```bash
.venv/bin/pytest tests/
```

### Step 2: Re-analyze Subspace Validation (Audited V2)
```bash
.venv/bin/python scripts/analyze_causal_subspace.py \
  --input results/circuit/sequence3_work/qwen25_subspace_validation_n32_eval.jsonl \
  --output-json results/circuit/sequence3_work/qwen25_subspace_validation_synthesis_audited_v2.json \
  --output-md results/circuit/sequence3_work/FINDINGS_QWEN25_CAUSAL_SUBSPACE_VALIDATION_AUDITED_V2.md \
  --mode validation
```

### Step 3: Re-analyze Subspace Confirmation (Exploratory Audited V2)
```bash
.venv/bin/python scripts/analyze_causal_subspace.py \
  --input results/circuit/sequence3_work/qwen25_subspace_confirmation_n80_eval.jsonl \
  --output-json results/circuit/sequence3_work/qwen25_subspace_confirmation_synthesis_exploratory_audited_v2.json \
  --output-md results/circuit/sequence3_work/FINDINGS_QWEN25_CAUSAL_SUBSPACE_CONFIRMATION_EXPLORATORY_AUDITED_V2.md \
  --mode exploratory
```

### Step 4: Re-analyze Behavioral Bridge (Paired Audited V2)
```bash
.venv/bin/python scripts/analyze_behavioral_bridge.py \
  --input results/circuit/sequence3_work/qwen25_behavioral_bridge_validation.jsonl \
  --output-json results/circuit/sequence3_work/qwen25_behavioral_bridge_synthesis_audited_v2.json \
  --output-md results/circuit/sequence3_work/FINDINGS_QWEN25_BEHAVIORAL_BRIDGE_AUDITED_V2.md
```

---

## 4. Key Audited Quantitative Tables (V2)

### Validation Residual Subspace (N=32 examples, 81/96 eligible cases)
All CIs are paired cluster-bootstrap 95% CIs ($B=1,000$, clustered by `example_id`):

| Rank $k$ | Causal Shift [95% CI] | Numerator Mean | Denominator Mean | Descriptive Recovery | Ratio Status | Random Margin | Qualifies |
|---|---|---|---|---|---|---|---|
| **$k=1$** | $+0.0120$ $[-0.0084, +0.0303]$ | $+0.0151$ | $-0.7126$ | $-2.12\%$ | `not_identifiable_under_policy` | $+0.26\%$ | **No** |
| **$k=2$** | $+0.0149$ $[-0.0112, +0.0407]$ | $+0.0142$ | $-0.7126$ | $-1.99\%$ | `not_identifiable_under_policy` | $-0.56\%$ | **No** |
| **$k=4$** | $+0.0129$ $[-0.0096, +0.0366]$ | $+0.0132$ | $-0.7126$ | $-1.85\%$ | `not_identifiable_under_policy` | $-0.30\%$ | **No** |
| **$k=8$** | $+0.0249$ $[+0.0030, +0.0459]$ | $+0.0282$ | $-0.7126$ | $-3.95\%$ | `not_identifiable_under_policy` | $-1.54\%$ | **No** |
| **$k=16$** | $+0.0208$ $[-0.0024, +0.0439]$ | $+0.0194$ | $-0.7126$ | $-2.72\%$ | `not_identifiable_under_policy` | $-1.11\%$ | **No** |
| **$k=32$** | $+0.0272$ $[+0.0047, +0.0486]$ | $+0.0249$ | $-0.7126$ | $-3.50\%$ | `not_identifiable_under_policy` | $-2.54\%$ | **No** |

*Prior Unregistered Policy Recovery*: Rank 1: $-2.12\%$ $[-27.88\%, 18.86\%]$; Rank 8: $-3.95\%$ $[-48.75\%, 40.75\%]$.  
*Selection Decision*: `optimal_rank: null`, `selection_outcome: no_rank_qualified`.

### Paired Behavioral Bridge Effects (N=32 examples, 96 cases across 32 clusters)

| Outcome Metric | Clean Baseline | Patched Subspace | Paired Diff [95% CI] | Transitions ($0\to 1$) | Behavioral Effect |
|---|---|---|---|---|---|
| **Answer EM** | $40.62\%$ | $40.62\%$ | $0.00\%$ $[0.00\%, 0.00\%]$ | 0 | None |
| **Cites Gold** | $11.46\%$ | $12.50\%$ | $+1.04\%$ $[-2.08\%, +4.17\%]$ | 2 | Not significant |
| **Cites Counterfactual** | $11.46\%$ | $11.46\%$ | $0.00\%$ $[0.00\%, 0.00\%]$ | 0 | **Null** |
| **Answer Correct + Cites CF** | $8.33\%$ | $8.33\%$ | $0.00\%$ $[0.00\%, 0.00\%]$ | 0 | **Null** |
| **Citation Precision [Continuous]** | $8.33\%$ | $7.92\%$ | $-0.42\%$ $[-3.02\%, +1.56\%]$ | N/A | Not significant |
| **Citation Recall [Continuous]** | $11.46\%$ | $12.50\%$ | $+1.04\%$ $[-2.08\%, +4.17\%]$ | N/A | Not significant |

*Behavioral Status*: `paired_behavioral_effect: null`. Zero citation redirections ($0 \to 1$) observed.

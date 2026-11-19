# Sequence 3 Scientific Audit (Version 2): Causal Component & Subspace Decomposition

**Date**: 2026-11-17  
**Time**: 05:00 IST (23:30 UTC)  
**Investigation**: Causal component-level circuit decomposition & post-evidence residual subspace localization across open-weights LLMs (Qwen 2.5 1.5B Instruct)  
**Audit Version**: V2 (incorporating explicit denominator identifiability policy, corrected confirmation denominator mean, and provenance amendment 002)  
**Terminal Registered Scientific Outcome**: `valid_negative_result`

---

## 1. Executive Summary & Terminal Outcome

A rigorous, versioned scientific audit of the Sequence 3 closed-loop investigation was conducted across statistical estimands, data provenance, preregistration fidelity, and confirmation gating.

Under the preregistered confirmatory protocol and the versioned post-audit analysis policy (Amendment 002):
- **Sequence 3A (Query Head Decomposition)** terminated as a **preregistered scientific null** because the whole attention mixer at citation prediction positions yielded a null causal shift ($+0.001$ $[-0.147, +0.179]$).
- **Sequence 3B (Post-Evidence Residual Subspace)** terminated as **no rank qualified** on the validation split. No evaluated rank ($k \in \{1, 2, 4, 8, 16, 32\}$) met the registered thresholds ($\ge 70.0\%$ donor recovery and $\ge 30.0\%$ margin over random basis).
- **Phase 6 (Behavioral Bridge)** terminated as a **null paired intervention effect** under free generation. Paired patched-minus-clean differences for answer correctness, counterfactual citations, and selective dissociation were all identically $0.00\%$ $[0.00\%, 0.00\%]$ with zero $0 \to 1$ transitions.
- **Terminal Registered Outcome**: **`valid_negative_result`**.

All raw experimental JSONLs, fitted basis weights, historical preregistrations, and v1 audited artifacts remain byte-identical. Formal preregistration amendments (`amendment_001.json` and `amendment_002.json`) document all protocol deviations and versioned sensitivity policies.

---

## 2. Authorization Basis & Protocol Integrity

### 2.1 Confirmation Authorization Basis
Antigravity operated under standing user authorization (`standing_user_instruction`) to proceed through the confirmation gate while the user was unavailable. This standing authorization establishes that execution access was authorized.

However, standing user authorization **does not cure scientific protocol deviations** from the registered selection rules or the confirmation command template.

### 2.2 Protocol Deviations Cataloged
- **DEV-01: Unregistered Fallback Rank Selection**: On validation ($N=32$, 96 cases), all ranks failed the preregistered criteria (recovery $\ge 70\%$, margin $\ge 30\%$). Applying an automatic fallback to rank 1 was unregistered; the protocol required reporting `optimal_rank: null` and `selection_outcome: no_rank_qualified`.
- **DEV-02: Rank Mismatch in Behavioral Bridge**: Behavioral free generation executed an ad-hoc intervention at rank 8, deviating from both the registered null outcome and the unregistered fallback rank 1.
- **DEV-03: Multi-Rank Confirmation Evaluation**: Confirmation evaluated five ranks ($k \in \{1, 4, 8, 16, 32\}$) instead of exactly one frozen rank, converting confirmatory inference into exploratory analysis and consuming the cohort.

---

## 3. Registered Confirmatory Outcomes (Audited V2)

All confidence intervals are paired cluster-bootstrap 95% CIs ($B=1,000$, clustered by `example_id`).

### 3.1 Sequence 3A: Attention Head Localization
- **Target**: Whole query-attention mixer at Layer 24 `pos_citation` under label swap.
- **Result**: Pooled causal shift $= +0.001$ $[-0.147, +0.179]$ (Structured: $-0.0003$, Random compact: $-0.0781$, UUID: $+0.0806$).
- **Preregistered Gate Decision**: Ineligible for head-level screening; branch terminated cleanly as a scientific null.

### 3.2 Sequence 3B: Residual Subspace Validation (Audited V2)
- **Target**: Post-evidence residual stream at Layer 14 `pos_post_evidence` ($N=32$, 96 cases; 81 eligible rows where $|d_{\text{donor}} - c_{\text{clean}}| > 0.5$).
- **Aggregate Denominator Mean**: $-0.7126$ across eligible cases (passes aggregate guard $\ge 0.5$).
- **Identifiability Policy (Amendment 002)**: Because bootstrap resamples exhibit denominator sign flips and cross below the 0.5 guard, recovery and margin ratios are marked `not_identifiable_under_policy` for inferential confidence intervals; point estimates are reported descriptively:
  - Rank 1: Causal shift $+0.0120$ $[-0.0084, +0.0303]$; Descriptive Recovery $-2.12\%$ [unidentifiable]; Descriptive Margin $+0.26\%$ [unidentifiable]; Qualifies: **No**.
  - Rank 2: Causal shift $+0.0149$ $[-0.0112, +0.0407]$; Descriptive Recovery $-1.99\%$ [unidentifiable]; Descriptive Margin $-0.56\%$ [unidentifiable]; Qualifies: **No**.
  - Rank 4: Causal shift $+0.0129$ $[-0.0096, +0.0366]$; Descriptive Recovery $-1.85\%$ [unidentifiable]; Descriptive Margin $-0.30\%$ [unidentifiable]; Qualifies: **No**.
  - Rank 8: Causal shift $+0.0249$ $[+0.0030, +0.0459]$; Descriptive Recovery $-3.95\%$ [unidentifiable]; Descriptive Margin $-1.54\%$ [unidentifiable]; Qualifies: **No**.
  - Rank 16: Causal shift $+0.0208$ $[-0.0024, +0.0439]$; Descriptive Recovery $-2.72\%$ [unidentifiable]; Descriptive Margin $-1.11\%$ [unidentifiable]; Qualifies: **No**.
  - Rank 32: Causal shift $+0.0272$ $[+0.0047, +0.0486]$; Descriptive Recovery $-3.50\%$ [unidentifiable]; Descriptive Margin $-2.54\%$ [unidentifiable]; Qualifies: **No**.
- **Historical Prior-Policy Values (Unregistered 80% Rule)**: Under the prior unregistered policy (which dropped unstable resamples), recovery point estimates and intervals were: Rank 1: $-2.12\%$ $[-27.88\%, 18.86\%]$; Rank 8: $-3.95\%$ $[-48.75\%, 40.75\%]$. Both policies confirm that no rank qualified.
- **Audited Selection Outcome**: `optimal_rank: null`, `selection_outcome: no_rank_qualified`.

### 3.3 Phase 6: Behavioral Bridge Free Generation (Audited V2)
- **Target**: Post-evidence subspace intervention (L14 Rank 8) during greedy autoregressive generation ($N=32$, 96 cases across 32 clusters).
- **Paired Causal Effects (Patched Minus Clean)**:
  - **Answer EM**: Clean $40.62\%$ vs Patched $40.62\%$ $\to$ Paired diff $= 0.00\%$ $[0.00\%, 0.00\%]$. Transitions: $0 \to 0: 57, 0 \to 1: 0, 1 \to 0: 0, 1 \to 1: 39$.
  - **Counterfactual Citation Rate**: Clean $11.46\%$ vs Patched $11.46\%$ $\to$ Paired diff $= 0.00\%$ $[0.00\%, 0.00\%]$. Transitions: $0 \to 0: 85, 0 \to 1: 0, 1 \to 0: 0, 1 \to 1: 11$.
  - **Correct Answer with Counterfactual Citation**: Clean $8.33\%$ vs Patched $8.33\%$ $\to$ Paired diff $= 0.00\%$ $[0.00\%, 0.00\%]$. Transitions: $0 \to 0: 88, 0 \to 1: 0, 1 \to 0: 0, 1 \to 1: 8$.
  - **Citation Precision [Continuous]**: Clean $8.33\%$ vs Patched $7.92\%$ $\to$ Paired diff $= -0.42\%$ $[-3.02\%, +1.56\%]$ (no binary transition table; precision is continuous).
  - **Gold Citation Rate**: Clean $11.46\%$ vs Patched $12.50\%$ $\to$ Paired diff $= +1.04\%$ $[-2.08\%, +4.17\%]$. Transitions: $0 \to 0: 83, 0 \to 1: 2, 1 \to 0: 1, 1 \to 1: 10$.
  - **Citation Recall [Continuous]**: Clean $11.46\%$ vs Patched $12.50\%$ $\to$ Paired diff $= +1.04\%$ $[-2.08\%, +4.17\%]$ (no binary transition table; recall is continuous).
- **Audited Outcome**: `paired_behavioral_effect: null`. Zero $0 \to 1$ citation redirection transitions occurred. The $11.46\%$ counterfactual citation rate and $8.33\%$ dissociation rate reflect pre-existing baseline generation errors present in the clean baseline without intervention.

---

## 4. Exploratory Confirmation Observations (Non-Confirmatory)

The confirmation cohort ($N=80$, 240 cases) was evaluated exploratorily across multiple ranks:
- **Eligible Cases**: 195/240 cases met the row threshold $|d_{\text{donor}} - c_{\text{clean}}| > 0.5$.
- **Correct Eligible Denominator Mean**: Calculated directly from raw rows, the aggregate denominator mean across the 195 eligible confirmation cases is **$-0.0955$** (not $-0.7042$, which was an erratum in historical audit draft text).
- **Ratio Identifiability under Versioned Policy**: Because the point denominator mean $|-0.0955| < 0.5$, it fails the aggregate guard. Ratios are undefined under the post-audit sensitivity policy (`ratio_status: denominator_below_aggregate_guard`), and `exploratory_best_margin_rank` is `null`.
- **Absolute Causal Shifts**: Modest positive logit shifts were observed across ranks:
  - Rank 1: $+0.0103$ $[-0.0024, +0.0229]$
  - Rank 4: $+0.0131$ $[+0.0018, +0.0266]$
  - Rank 8: $+0.0297$ $[+0.0170, +0.0430]$
  - Rank 16: $+0.0321$ $[+0.0188, +0.0486]$
  - Rank 32: $+0.0289$ $[+0.0136, +0.0464]$
- **Historical Prior-Policy Ratio Values**: Under the former policy without an aggregate denominator guard, recovery was reported as Rank 1: $-12.83\%$, Rank 8: $-31.27\%$, Rank 16: $-32.35\%$. These negative ratios were an artifact of small negative denominators cancelling against positive projection shifts.
- All qualification flags are **False**. Confirmation data are exploratory and consumed.

---

## 5. Scope & Scientific Boundaries

The findings of this investigation are strictly limited to the tested configuration:
1. **Narrow Scope of Negative Result**: The tested orthonormal basis fitted on discovery difference vectors at Layer 14 `pos_post_evidence` failed the preregistered causal recovery and margin criteria.
2. **No Overbroad General Claim**: This negative result does **not** prove that binding subspaces or citation routing circuits do not exist in LLMs. It demonstrates only that the specific linear difference basis at Layer 14 post-evidence does not causally isolate the evidence-binding handle under the tested protocol.
3. **Format Heterogeneity**: The basis was fitted jointly across structured, compact, and UUID formats. Format-specific representations require leave-one-format-out fitting and fresh disjoint confirmatory testing.

---

## 6. Prohibited Unsupported Claims

| Prohibited Claim | Reason for Prohibition |
|---|---|
| `validated_partial_mechanism` | No rank met the registered validation thresholds; confirmation was exploratory. |
| *Successful causal binding recovery* | Recovery ratios were negative or undefined under conservative denominator policy. |
| *Confirmed rank-8 subspace* | Confirmation evaluated 5 ranks post-hoc without a qualified frozen rank; all qualification flags false. |
| *Behavioral citation redirection* | Paired intervention effect was identically $0.00\%$; zero $0 \to 1$ transitions observed. |
| *Cross-format transfer failure* | Basis was fitted jointly on all formats, not evaluated leave-one-format-out. |
| *Absence of binding mechanisms in transformers* | Null result is limited to tested Layer 14 post-evidence linear basis in Qwen 2.5 1.5B. |

---

## 7. Blog Integration Gate

> [!WARNING]
> **BLOG INTEGRATION IS BLOCKED**:  
> No blog post (`blog/symbolic-ir-engineering-blog.md`), site file (`blog/site/index.html`), or public figure may be edited to reflect Sequence 3 until human review of this scientific audit is complete.

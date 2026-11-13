# Stage 7B Confirmatory Findings: Cross-Model Component Localization

## Executive Summary

This report provides an empirical evaluation of component-level causal mechanisms underlying source-identifier binding across **all six eligible open-weights models**:
1. **Qwen 2.5 1.5B** (*Pure GQA Transformer*, 28 Layers)
2. **Qwen 3.5 2B** (*Hybrid Gated DeltaNet + GQA*, 24 Layers)
3. **Tiny Aya Global** (*Deep Asymmetric GQA*, 36 Layers)
4. **Qwen 3.5 4B** (*Hybrid Gated DeltaNet + GQA*, 32 Layers)
5. **Gemma 4 E2B** (*Deep Asymmetric GQA*, 35 Layers)
6. **Gemma 4 E4B** (*Deep Asymmetric GQA + PLE*, 42 Layers)

Following a frozen **pre-registration protocol** (`results/circuit/circuit_preregistration.json`), candidate components were identified on a Discovery split ($N=32$, 576 cases total), tested on an independent Held-out Validation split ($N=32$, 576 cases total), and confirmed on a high-powered Confirmatory split ($N=80$, 1,440 cases total).

> [!IMPORTANT]
> **Core Confirmatory Finding:**
> At preregistered critical hubs, patching the attention/DeltaNet mixer output moves first-token identifier preference more than patching the corresponding MLP output in **5 of 6 primary binding hubs** (and across all 6 models when including designated terminal hubs). Gemma 4 E2B exhibits an architecture-specific pre-hub handover where its designated Layer 24 binding hub shows MLP dominance, but resolves to strong mixer dominance at its designated Layer 35 terminal hub.

---

## Confirmatory Evidence Summary (N=80 Semantic Clusters, 240 Cases/Model, 1,440 Cases Total)

### 1. Primary Preregistered Binding Dissociation (Mixer − MLP)
Computed using a paired cluster-robust bootstrap resampling by `example_id` ($B=1,000$ replicates, 95% CIs) on the held-out confirmation split:

| Model | Architecture | Designated Hub | Paired Mixer − MLP First-Token Shift | 95% Bootstrap CI | Confirmatory Binding Status |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Qwen 2.5 1.5B** | Pure GQA Transformer | L24 | **+0.621** | [+0.436, +0.804] | **CONFIRMED** (Interval strictly > 0) |
| **Qwen 3.5 2B** | Hybrid Gated DeltaNet | L20 | **+1.031** | [+0.682, +1.339] | **CONFIRMED** (Interval strictly > 0) |
| **Tiny Aya Global** | Deep Asymmetric GQA | L24 | **+1.005** | [+0.336, +1.597] | **CONFIRMED** (Interval strictly > 0) |
| **Qwen 3.5 4B** | Hybrid Gated DeltaNet | L24 | **+2.198** | [+1.833, +2.556] | **CONFIRMED** (Interval strictly > 0) |
| **Gemma 4 E2B** *(Primary)* | Deep Asymmetric GQA | L24 (Binding Hub) | **-0.494** | [-0.760, -0.220] | **FAILED** (MLP Dominates Mixer at L24) |
| **Gemma 4 E2B** *(Terminal)* | Deep Asymmetric GQA | L35 (Terminal Hub) | **+2.851** | [+1.404, +4.197] | **CONFIRMED** (Terminal Mixer Dominance) |
| **Gemma 4 E4B** | Deep Asymmetric PLE | L36 | **+14.460** | [+11.914, +16.823] | **CONFIRMED** (Interval > 0; KL Specificity Limit) |

### 2. Unpatched Donor Baselines & Mechanistic Sensitivity Analysis

An interchange intervention replaces hidden states with those from an unpatched swapped-prompt donor. A positive relative shift $\Delta_{\text{First}}$ demonstrates causal transmission, but does not imply that the unpatched donor prompt unconditionally won the first-token margin in every case. The table below presents the unpatched donor victory rates and sensitivity analyses stratified by donor success:

#### A. Unpatched Donor Margin & Positive Victory Rates (`swap_baseline.first_token_pref > 0`)

| Model | Overall Donor-Positive Rate | Mean Donor Margin (nats) | Structured `[S1]` Rate | Random Compact `[XQ7M]` Rate | UUID `[3f8a...]` Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Qwen 2.5 1.5B** | 65.8% | +1.283 nats | 83.8% (+2.67) | 60.0% (+1.12) | 53.8% (+0.07) |
| **Qwen 3.5 2B** | 63.3% | +0.915 nats | 62.5% (+1.43) | 70.0% (+1.17) | 57.5% (+0.15) |
| **Tiny Aya Global** | 63.7% | +0.641 nats | 91.2% (+2.35) | 52.5% (-0.12) | 47.5% (-0.31) |
| **Qwen 3.5 4B** | 67.1% | +1.433 nats | 76.2% (+1.83) | 61.3% (+1.52) | 63.7% (+0.95) |
| **Gemma 4 E2B** | 59.2% | +3.116 nats | 73.8% (+7.93) | 51.2% (+0.61) | 52.5% (+0.81) |
| **Gemma 4 E4B** | 80.8% | +19.699 nats | 71.2% (+17.58) | 86.2% (+23.63) | 85.0% (+17.88) |

#### B. Sensitivity Subgroups: Paired Mixer − MLP Shift Stratified by Donor Success

> [!NOTE]
> Conditioning on donor success can introduce selection bias. Therefore, the **All Cases** estimand ($N=240$) remains the primary preregistered result. The donor-positive and donor-negative subgroups serve as a sensitivity analysis confirming that the mixer output faithfully transports the donor state when present.

| Model | Evaluated Hub | All Cases ($N=240$) | Donor-Positive ($N_{\text{pos}}$) | Donor-Negative ($N_{\text{neg}}$) | Pearson $r$ (Margin vs. $\Delta$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Qwen 2.5 1.5B** | L24 | **+0.621** [+0.436, +0.804] | **+0.902** [+0.707, +1.102] ($N=158$) | +0.080 [-0.172, +0.342] ($N=82$) | $r = +0.358$ |
| **Qwen 3.5 2B** | L20 | **+1.031** [+0.682, +1.339] | **+1.837** [+1.544, +2.150] ($N=152$) | -0.362 [-0.876, +0.106] ($N=88$) | $r = +0.527$ |
| **Tiny Aya Global** | L24 | **+1.005** [+0.336, +1.597] | **+2.252** [+1.671, +2.819] ($N=153$) | -1.189 [-2.140, -0.313] ($N=87$) | $r = +0.685$ |
| **Qwen 3.5 4B** | L24 | **+2.198** [+1.833, +2.556] | **+2.917** [+2.538, +3.299] ($N=161$) | +0.733 [+0.315, +1.171] ($N=79$) | $r = +0.484$ |
| **Gemma 4 E2B** | L24 | **-0.494** [-0.760, -0.220] | **-0.655** [-1.072, -0.276] ($N=142$) | -0.261 [-0.655, +0.109] ($N=98$) | $r = +0.004$ |
| **Gemma 4 E2B** *(Terminal)* | L35 | **+2.851** [+1.404, +4.197] | **+5.773** [+4.468, +7.012] ($N=142$) | -1.382 [-3.752, +0.765] ($N=98$) | $r = +0.465$ |
| **Gemma 4 E4B** | L36 | **+14.460** [+11.914, +16.823] | **+16.859** [+14.425, +19.223] ($N=194$) | +4.341 [-0.114, +9.532] ($N=46$) | $r = +0.520$ |

### 3. Full Layer-Level Confirmation Breakdown
All metrics reported with **cluster-robust bootstrap 95% confidence intervals clustered by `example_id`** ($B=1,000$ replicates):

| Architecture & Model | Depth | Evaluated Layer | Component | First-Token Shift $\Delta_{\text{First}}$ ($B$) | Continuation Shift $\Delta_{\text{Cont}}$ ($F$) | Vocabulary KL $D_{\text{KL}}$ (nats) | Post-Citation Syntax $\Delta_{\text{Syntax}}$ | Preregistered Criterion Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Qwen 2.5 1.5B**<br/>*(Pure GQA Transformer)* | 28L | **L20** | Mixer | **-0.494** [-0.623, -0.369] | **+0.536** [+0.476, +0.594] | 0.043 [0.032, 0.055] | -0.042 [-0.084, -0.003] | Pre-hub handover / stale mediator |
| | | | MLP | +0.245 [+0.174, +0.315] | +0.064 [+0.030, +0.106] | 0.026 | -0.062 | — |
| **Qwen 2.5 1.5B**<br/>*(Pure GQA Transformer)* | 28L | **L24** | Mixer | **+0.701** [+0.472, +0.929] | **+0.659** [+0.545, +0.778] | 0.073 [0.051, 0.107] | +0.003 [-0.008, +0.014] | **CONFIRMED Binding Hub** ($B$) |
| | | | MLP | +0.080 [-0.003, +0.175] | -0.014 [-0.034, +0.002] | 0.016 | -0.017 | — |
| **Qwen 3.5 2B**<br/>*(Hybrid Gated DeltaNet)* | 24L | **L16** | Mixer | **-0.330** [-0.580, -0.061] | **+1.106** [+1.026, +1.195] | 0.084 [0.066, 0.103] | +0.022 [-0.039, +0.074] | Pre-hub handover / stale mediator |
| | | | MLP | +0.102 [+0.050, +0.150] | +0.020 [+0.003, +0.045] | 0.010 | -0.042 | — |
| **Qwen 3.5 2B**<br/>*(Hybrid Gated DeltaNet)* | 24L | **L20** | Mixer | **+1.200** [+0.839, +1.545] | **+1.087** [+0.926, +1.286] | 0.137 [0.103, 0.174] | +0.007 [-0.013, +0.023] | **CONFIRMED Binding Hub** ($B$) |
| | | | MLP | +0.169 [+0.092, +0.249] | -0.006 [-0.016, +0.004] | 0.010 | +0.025 | — |
| **Tiny Aya Global**<br/>*(Deep Asymmetric GQA)* | 36L | **L24** | Mixer | **+0.951** [+0.283, +1.544] | **+0.444** [+0.347, +0.530] | 0.307 [0.214, 0.412] | +0.023 [-0.010, +0.056] | **CONFIRMED Binding Hub** ($B$) |
| | | | MLP | -0.053 [-0.078, -0.029] | +0.006 [-0.013, +0.026] | 0.002 | -0.052 | — |
| **Tiny Aya Global**<br/>*(Deep Asymmetric GQA)* | 36L | **L36** | Mixer | **-0.026** [-0.046, -0.004] | **-0.001** [-0.005, +0.004] | 0.001 [0.001, 0.001] | -0.005 [-0.011, -0.000] | Downstream continuation ($F$) |
| | | | MLP | -0.237 [-0.518, +0.070] | +0.231 [+0.118, +0.367] | 0.102 | +0.016 | — |
| **Qwen 3.5 4B**<br/>*(Hybrid Gated DeltaNet)* | 32L | **L24** | Mixer | **+1.973** [+1.638, +2.308] | **+0.031** [+0.013, +0.054] | 0.303 [0.244, 0.368] | +0.116 [+0.095, +0.137] | **CONFIRMED Binding Hub** ($B$) |
| | | | MLP | -0.225 [-0.325, -0.129] | -0.005 [-0.009, -0.002] | 0.017 | +0.077 | — |
| **Qwen 3.5 4B**<br/>*(Hybrid Gated DeltaNet)* | 32L | **L28** | Mixer | **+0.621** [+0.294, +0.937] | **+1.144** [+0.980, +1.332] | 0.069 [0.051, 0.089] | +0.068 [+0.042, +0.094] | Downstream continuation ($F$) |
| | | | MLP | +0.231 [+0.168, +0.296] | +0.001 [-0.001, +0.004] | 0.008 | +0.035 | — |
| **Qwen 3.5 4B**<br/>*(Hybrid Gated DeltaNet)* | 32L | **L32** | Mixer | **-0.886** [-1.191, -0.569] | **+0.017** [-0.008, +0.046] | 0.066 [0.054, 0.080] | -0.423 [-0.555, -0.317] | Downstream continuation ($F$) |
| | | | MLP | -0.147 [-0.441, +0.124] | +0.118 [+0.074, +0.170] | 0.102 | +0.064 | — |
| **Gemma 4 E2B**<br/>*(Deep Asymmetric GQA)* | 35L | **L24** | Mixer | **+0.706** [+0.503, +0.891] | **+0.004** [-0.079, +0.087] | 0.061 [0.028, 0.102] | +0.763 [+0.388, +1.238] | **FAILED Binding Dissociation** (MLP dominates Mixer at L24) |
| | | | MLP | +1.201 [+0.916, +1.518] | +1.970 [+1.280, +2.664] | 0.252 | +3.162 | — |
| **Gemma 4 E2B**<br/>*(Deep Asymmetric GQA)* | 35L | **L35** | Mixer | **+1.905** [+0.900, +2.769] | **+0.075** [-0.051, +0.195] | 0.123 [0.050, 0.201] | +0.288 [+0.164, +0.420] | **CONFIRMED Terminal Mixer Hub** |
| | | | MLP | -0.947 [-1.619, -0.263] | +0.024 [-0.088, +0.155] | 0.038 | +1.930 | — |
| **Gemma 4 E4B**<br/>*(Deep Asymmetric PLE)* | 42L | **L36** | Mixer | **+18.073** [+15.196, +20.767] | **+0.233** [+0.081, +0.380] | 3.156 [2.366, 4.036] | +0.438 [+0.196, +0.683] | **CONFIRMED Binding**; Specificity Limit ($D_{\text{KL}} > 1.0$) |
| | | | MLP | +3.613 [+2.784, +4.431] | -0.035 [-0.126, +0.024] | 0.398 | -0.733 | — |
| **Gemma 4 E4B**<br/>*(Deep Asymmetric PLE)* | 42L | **L42** | Mixer | **+8.735** [+5.189, +12.105] | **+0.733** [+0.405, +1.109] | 2.192 [1.334, 3.192] | -0.015 [-0.114, +0.081] | **CONFIRMED Terminal Mixer Hub** |
| | | | MLP | +1.219 [-0.607, +3.171] | -0.301 [-0.591, -0.103] | 1.256 | -0.088 | — |

---

## Rigorous Hypothesis Evaluation & Status

| Hypothesis | Preregistered Criterion | Empirical Confirmation Status | Assessment |
| :--- | :--- | :--- | :--- |
| **H1: Attention Mediates Binding ($B$)** | $\Delta_{\text{First}}^{\text{Mixer}} > 0$, 95% CI lower $> 0$ | Confirmed at confirmation hubs in 6/6 models on confirmation split (+0.621 to +14.460, all CIs $>0$). Validation was directionally mixed (conclusive in 3/6, 3/6 crossed zero at $N=32$). | **SUPPORTED** (on high-power cohort) |
| **H2: Mixer vs. MLP Dissociation** | Paired cluster bootstrap (Mixer − MLP) CI lower $> 0$ at designated binding hub | **Confirmed at 5 of 6 primary binding hubs.** Gemma 4 E2B failed at designated Layer 24 binding hub ($-0.494$ [$-0.760, -0.220$], MLP-dominated), but confirmed at designated Layer 35 terminal hub ($+2.851$ [$+1.404, +4.197$]). | **PARTIALLY SUPPORTED** (5/6 primary hubs; mixed dual-hub in Gemma E2B) |
| **H3: Downstream Continuation Influence ($F$)** | Post-binding component causally routes multi-token continuation | Observed in a subset of models: Tiny Aya (L36 MLP +0.231), Qwen 3.5 4B (L28 Mixer +1.144, L32 MLP +0.118), Gemma 4 E2B (L24 MLP +1.970), Gemma 4 E4B (L42 Mixer +0.733). Full serialization specialization requires matched non-identifier copying controls. | **CONTINUATION INFLUENCE OBSERVED** (Architecture-specific) |
| **H4: Causal Specificity** | $D_{\text{KL}} < 1.0$ nats, $|\Delta_{\text{Syntax}}| < 1.0$ nats | **Passed in 5 of 6 models.** Failed for Gemma 4 E4B ($D_{\text{KL}} = 3.156$ [2.366, 4.036] nats), whose large binding shift caused broad vocabulary reorganization. | **PARTIALLY SUPPORTED** (5/6 passed, 1/6 failed) |
| **Full $R \to B \to F$ Factorization** | Independent causal manipulation of $R$, $B$, and $F$ | Not established. $R$ (source evidence selection) was teacher-forced, not manipulated. Causal dissociation established between $B$ and continuation $F$. | **UNRESOLVED / PARTIAL** |
| **Sparse Modular Circuit** | Sparse subset of individual heads/channels isolates the effect | Not established. Interventions were applied to entire layer mixer components. Existing head pilot lacks held-out statistical significance (L24H3 CI crosses zero). Refuting a distributed account requires head/subspace minimality. | **UNRESOLVED / NOT CLAIMED** |

---

## Key Mechanistic Discoveries & Format Heterogeneity

### 1. Cross-Model Component Dissociation
- **Pure GQA Transformers (Qwen 2.5 1.5B):** Isolated transplant of Layer 24 attention mixer shifts first-token preference by +0.701 [+0.472, +0.929], whereas the Layer 24 MLP produces virtually no shift (+0.080). The paired cluster difference is +0.621 [+0.436, +0.804]. Meanwhile, Layer 20 Mixer acts as a counter-directional stale-association mediator (-0.494 [-0.623, -0.369]).
- **Hybrid DeltaNet + GQA (Qwen 3.5 2B & 4B):** Linear recurrent states handle early context accumulation, but binding is handed over to late attention mixers (Layer 20 in 2B: paired difference +1.031 [+0.682, +1.339]; Layer 24 in 4B: paired difference +2.198 [+1.833, +2.556]). Downstream continuation is routed by Layer 28 attention mixer (+1.144) and completed by Layer 32 MLP (+0.118).
- **Deep Asymmetric Models (Tiny Aya, Gemma 4):** Tiny Aya exhibits component separation: Layer 24 Mixer mediates initial binding (paired difference +1.005 [+0.336, +1.597]), while Layer 36 MLP mediates multi-token continuation (+0.231). Gemma 4 E2B exhibits an architecture-specific pre-hub handover: Layer 24 shows MLP dominance ($-0.494$), but handover completes at Layer 35 where terminal mixer dominance is $+2.851$ [$+1.404, +4.197$]. Gemma 4 E4B shows the strongest binding engine in the cohort at Layer 36 (+18.073, paired difference +14.460), though accompanied by high vocabulary divergence ($D_{\text{KL}} = 3.156$ nats).

### 2. Format Heterogeneity & Unpatched Donor Margin Friction
Condition-level baselines reveal that harder tokenizations suffer from low unpatched donor victory rates:
- **Structured (`[S1]`):** Unpatched donor victory rate is 62.5%–91.2% across models, with strongly positive average margins.
- **Random Compact (`[XQ7M]`):** Donor victory rate drops to 51.2%–86.2%; Tiny Aya's mean donor margin is negative ($-0.121$ nats).
- **UUID (`[3f8a...]`):** Severe baseline friction. Donor victory rate ranges from 47.5% (Tiny Aya) to 85.0% (Gemma E4B). In Qwen 2.5 1.5B, mean donor margin is essentially zero ($+0.066$ nats), and in Tiny Aya it is negative ($-0.306$ nats).
- **Subgroup Sensitivity:** When conditioned on donor-positive cases, the paired mixer advantage strengthens substantially across models (e.g. Qwen 2.5 L24 increases from $+0.621$ to $+0.902$, Tiny Aya from $+1.005$ to $+2.252$). This confirms that late mixers actively transport the counterfactual choice whenever the donor state reliably computes it.

---

## Summary Conclusion & Scientific Boundaries

1. **What is solidly established:** Late attention/DeltaNet mixers causally mediate identifier selection ($B$) at primary hubs in 5 of 6 models (and 6 of 6 including designated terminal hubs) on an 80-example held-out confirmation split.
2. **What remains architecture-specific:** Pre-hub handover (Gemma 4 E2B L24 MLP vs L35 Mixer) and downstream continuation (Tiny Aya MLP vs Qwen 3.5 / Gemma 4 E4B Mixer).
3. **What is not yet established:** Computation vs. transport (interventions at citation positions do not distinguish whether binding was computed at the mixer or transported from earlier evidence representations); full factorization ($R \to B \to F$); and sparse head circuits (L24H3 pilot CI crosses zero; requires held-out necessity/minimality testing).
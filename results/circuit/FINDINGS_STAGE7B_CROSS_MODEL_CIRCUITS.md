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
> Across all six models, preregistered late mixer components causally shift first-token identifier preference more strongly than matched MLP components on the 80-example held-out confirmation cohort. The magnitude and downstream continuation mechanism vary substantially by architecture.

---

## Confirmatory Evidence Summary (N=80 Semantic Clusters, 240 Cases/Model, 1,440 Cases Total)

### 1. Primary Preregistered Binding Dissociation (Mixer − MLP)
Computed using a paired cluster-robust bootstrap resampling by `example_id` ($B=1,000$ replicates, 95% CIs) on the held-out confirmation split:

| Model | Architecture | Hub Layer | Paired Mixer − MLP First-Token Shift | 95% Bootstrap CI | Confirmatory Binding Result |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Qwen 2.5 1.5B** | Pure GQA Transformer | L24 | **+0.621** | [+0.436, +0.804] | **CONFIRMED** (Interval strictly > 0) |
| **Qwen 3.5 2B** | Hybrid Gated DeltaNet | L20 | **+1.031** | [+0.682, +1.339] | **CONFIRMED** (Interval strictly > 0) |
| **Tiny Aya Global** | Deep Asymmetric GQA | L24 | **+1.005** | [+0.336, +1.597] | **CONFIRMED** (Interval strictly > 0) |
| **Qwen 3.5 4B** | Hybrid Gated DeltaNet | L24 | **+2.198** | [+1.833, +2.556] | **CONFIRMED** (Interval strictly > 0) |
| **Gemma 4 E2B** | Deep Asymmetric GQA | L35 | **+2.851** | [+1.404, +4.197] | **CONFIRMED** (Interval strictly > 0) |
| **Gemma 4 E4B** | Deep Asymmetric PLE | L36 | **+14.460** | [+11.914, +16.823] | **CONFIRMED** (Interval strictly > 0) |

### 2. Full Layer-Level Confirmation Breakdown
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
| **Tiny Aya Global**<br/>*(Deep Asymmetric GQA)* | 36L | **L36** | Mixer | **-0.026** [-0.046, -0.004] | **-0.001** [-0.005, +0.004] | 0.001 [0.001, 0.001] | -0.005 [-0.011, -0.000] | Downstream serialization ($F$) |
| | | | MLP | -0.237 [-0.518, +0.070] | +0.231 [+0.118, +0.367] | 0.102 | +0.016 | — |
| **Qwen 3.5 4B**<br/>*(Hybrid Gated DeltaNet)* | 32L | **L24** | Mixer | **+1.973** [+1.638, +2.308] | **+0.031** [+0.013, +0.054] | 0.303 [0.244, 0.368] | +0.116 [+0.095, +0.137] | **CONFIRMED Binding Hub** ($B$) |
| | | | MLP | -0.225 [-0.325, -0.129] | -0.005 [-0.009, -0.002] | 0.017 | +0.077 | — |
| **Qwen 3.5 4B**<br/>*(Hybrid Gated DeltaNet)* | 32L | **L28** | Mixer | **+0.621** [+0.294, +0.937] | **+1.144** [+0.980, +1.332] | 0.069 [0.051, 0.089] | +0.068 [+0.042, +0.094] | Downstream serialization ($F$) |
| | | | MLP | +0.231 [+0.168, +0.296] | +0.001 [-0.001, +0.004] | 0.008 | +0.035 | — |
| **Qwen 3.5 4B**<br/>*(Hybrid Gated DeltaNet)* | 32L | **L32** | Mixer | **-0.886** [-1.191, -0.569] | **+0.017** [-0.008, +0.046] | 0.066 [0.054, 0.080] | -0.423 [-0.555, -0.317] | Downstream serialization ($F$) |
| | | | MLP | -0.147 [-0.441, +0.124] | +0.118 [+0.074, +0.170] | 0.102 | +0.064 | — |
| **Gemma 4 E2B**<br/>*(Deep Asymmetric GQA)* | 35L | **L24** | Mixer | **+0.706** [+0.503, +0.891] | **+0.004** [-0.079, +0.087] | 0.061 [0.028, 0.102] | +0.763 [+0.388, +1.238] | Pre-hub handover / stale mediator |
| | | | MLP | +1.201 [+0.916, +1.518] | +1.970 [+1.280, +2.664] | 0.252 | +3.162 | — |
| **Gemma 4 E2B**<br/>*(Deep Asymmetric GQA)* | 35L | **L35** | Mixer | **+1.905** [+0.900, +2.769] | **+0.075** [-0.051, +0.195] | 0.123 [0.050, 0.201] | +0.288 [+0.164, +0.420] | **CONFIRMED Binding Hub** ($B$) |
| | | | MLP | -0.947 [-1.619, -0.263] | +0.024 [-0.088, +0.155] | 0.038 | +1.930 | — |
| **Gemma 4 E4B**<br/>*(Deep Asymmetric PLE)* | 42L | **L36** | Mixer | **+18.073** [+15.196, +20.767] | **+0.233** [+0.081, +0.380] | 3.156 [2.366, 4.036] | +0.438 [+0.196, +0.683] | **CONFIRMED Binding**; Specificity Limit ($D_{\text{KL}} > 1.0$) |
| | | | MLP | +3.613 [+2.784, +4.431] | -0.035 [-0.126, +0.024] | 0.398 | -0.733 | — |
| **Gemma 4 E4B**<br/>*(Deep Asymmetric PLE)* | 42L | **L42** | Mixer | **+8.735** [+5.189, +12.105] | **+0.733** [+0.405, +1.109] | 2.192 [1.334, 3.192] | -0.015 [-0.114, +0.081] | Downstream serialization ($F$) |
| | | | MLP | +1.219 [-0.607, +3.171] | -0.301 [-0.591, -0.103] | 1.256 | -0.088 | — |

---

## Rigorous Hypothesis Evaluation & Status

| Hypothesis | Preregistered Criterion | Empirical Confirmation Status | Assessment |
| :--- | :--- | :--- | :--- |
| **H1: Attention Mediates Binding ($B$)** | $\Delta_{\text{First}}^{\text{Mixer}} > 0$, 95% CI lower $> 0$ | Confirmed in 6/6 models on confirmation split (+0.701 to +18.073, all CIs $>0$). Validation was directionally mixed (conclusive in 3/6, 3/6 crossed zero at $N=32$). | **SUPPORTED** (on high-power cohort) |
| **H2: Mixer vs. MLP Dissociation** | Paired cluster bootstrap (Mixer − MLP) CI lower $> 0$ | Confirmed in 6/6 models on confirmation split (Paired differences +0.621 to +14.460, all CIs strictly $>0$). | **SUPPORTED** |
| **H3: Downstream Serialization ($F$)** | Post-binding component routes multi-token continuation | Confirmed in a subset of models: Tiny Aya (L36 MLP +0.231 [+0.118, +0.367]), Qwen 3.5 4B (L28 Mixer +1.144, L32 MLP +0.118), Gemma 4 E2B (L24 MLP +1.970), Gemma 4 E4B (L42 Mixer +0.733). | **SUPPORTED in a subset** (Architecture-specific) |
| **H4: Causal Specificity** | $D_{\text{KL}} < 1.0$ nats, $|\Delta_{\text{Syntax}}| < 1.0$ nats | **Passed in 5 of 6 models.** Failed for Gemma 4 E4B ($D_{\text{KL}} = 3.156$ [2.366, 4.036] nats), whose large binding shift caused broad vocabulary reorganization. | **PARTIALLY SUPPORTED** (5/6 passed, 1/6 failed) |
| **Full $R \to B \to F$ Factorization** | Independent causal manipulation of $R$, $B$, and $F$ | Not established. $R$ (source evidence selection) was teacher-forced, not manipulated. Causal dissociation established between $B$ and $F$. | **UNRESOLVED / PARTIAL** |
| **Sparse Modular Circuit** | Sparse subset of individual heads/channels isolates the effect | Not established. Interventions were applied to entire layer mixer components. Refuting a distributed account requires head/subspace minimality. | **UNRESOLVED / NOT CLAIMED** |

---

## Key Mechanistic Discoveries & Format Heterogeneity

### 1. Cross-Model Component Dissociation
- **Pure GQA Transformers (Qwen 2.5 1.5B):** Isolated transplant of Layer 24 attention mixer shifts first-token preference by +0.701 [+0.472, +0.929], whereas the Layer 24 MLP produces virtually no shift (+0.080). The paired cluster difference is +0.621 [+0.436, +0.804]. Meanwhile, Layer 20 Mixer acts as a counter-directional stale-association mediator (-0.494 [-0.623, -0.369]).
- **Hybrid DeltaNet + GQA (Qwen 3.5 2B & 4B):** Linear recurrent states handle early-to-mid context accumulation, but binding is handed over abruptly to late full-attention mixers (Layer 20 in 2B: paired difference +1.031 [+0.682, +1.339]; Layer 24 in 4B: paired difference +2.198 [+1.833, +2.556]). Downstream continuation is routed by Layer 28 attention mixer (+1.144) and completed by Layer 32 MLP (+0.118).
- **Deep Asymmetric Models (Tiny Aya, Gemma 4):** Tiny Aya exhibits clean component separation: Layer 24 Mixer mediates initial binding (paired difference +1.005 [+0.336, +1.597]), while Layer 36 MLP mediates multi-token continuation (+0.231). Gemma 4 E4B shows the strongest binding engine in the cohort at Layer 36 (+18.073, paired difference +14.460), though accompanied by high vocabulary divergence ($D_{\text{KL}} = 3.156$ nats).

### 2. Format Heterogeneity & Direct-Swap Baselines
While the aggregate confirmation effect is strongly positive across all six models, condition-level baselines reveal format-specific constraints:
- **Structured (`[S1]`):** Produces positive baseline direct-swap effects across all six models (+1.259 to +40.191).
- **Random Compact (`[XQ7M]`):** Positive in five models; Gemma 4 E2B interval crosses zero (+2.705 [-0.629, +5.837]).
- **UUID (`[3f8a...]`):** Exhibits substantial friction. In Qwen 2.5 1.5B, the UUID direct-swap interval crosses zero (-0.067 [-0.969, +0.798]). In Tiny Aya Global, the UUID direct-swap effect is strictly negative (-1.721 [-3.457, -0.119]), reflecting strong persistence of prior associations under high-entropy token sequences.

---

## Summary Conclusion

1. **What is solidly established:** Late attention/mixer components causally mediate identifier selection ($B$) across all six tested architectures on an 80-example held-out confirmation split, showing statistically significant dissociation over matched MLPs.
2. **What remains architecture-specific:** Identifier continuation ($F$) is mediated downstream by attention mixers in some architectures (Qwen 3.5 4B, Gemma 4 E4B) and MLPs in others (Tiny Aya).
3. **What is not yet established:** Full three-stage factorization ($R \to B \to F$) requires independent manipulation of the source-selection step ($R$); a sparse sub-network or head-level circuit requires held-out head ablations and minimality testing.
# Stage 7: causal source-to-identifier binding

**Design:** 8 semantic examples × 3 identifier formats = 24 paired source-ID swaps and 384 activation interventions on `CohereLabs/tiny-aya-global`. Prompts contain 2411–3640 tokens. The relevant source swaps identifiers with a distractor while source text, question, answer, and the identifier set remain fixed.

The primary direct effect is the change in `log P(swapped ID) - log P(original ID)` after the prompt swap. The patching effect is the same preference change after transplanting a state from the swapped run into the clean run. Intervals are 5,000-replicate paired bootstraps over semantic examples.

## Direct source-ID swap

| Identifier | Total log-probability effect | Per-token effect | Positive cases |
|---|---:|---:|---:|
| [S1] | 2.171 [0.481, 3.842] | 0.543 [0.111, 0.970] | 7/8 |
| [XQ7M] | 5.380 [1.660, 9.083] | 1.223 [0.345, 2.138] | 6/8 |
| UUID | 7.562 [0.826, 14.729] | 0.304 [0.023, 0.606] | 6/8 |

A positive value means the same semantic source becomes more likely to be cited with its new identifier after the swap. The model shows correct causal rebinding in at least two formats: the same semantic source becomes more likely to be cited with its new identifier, although no fact or answer changed.

## Citation-state activation patching

The citation-context intervention patches every residual state that predicts a token of the candidate identifier. Layer 1 is an early control; the other layers cover the Stage 6 binding/output regions.

| Identifier | Layer | Total patch effect | Per-token patch effect | Aggregate recovery |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.069 [-0.123, -0.022] | -0.017 [-0.031, -0.006] | -3.2% |
| [S1] | 12 | 0.682 [0.120, 1.211] | 0.170 [0.028, 0.304] | 31.4% |
| [S1] | 24 | 1.771 [-0.043, 3.726] | 0.443 [-0.011, 0.929] | 81.6% |
| [S1] | 36 | 2.171 [0.408, 3.897] | 0.543 [0.113, 0.972] | 100.0% |
| [XQ7M] | 1 | -0.017 [-0.073, 0.033] | -0.004 [-0.018, 0.008] | -0.3% |
| [XQ7M] | 12 | 0.579 [-1.129, 2.387] | 0.124 [-0.261, 0.587] | 10.8% |
| [XQ7M] | 24 | 4.359 [1.916, 6.651] | 0.969 [0.414, 1.501] | 81.0% |
| [XQ7M] | 36 | 5.380 [1.804, 8.906] | 1.223 [0.327, 2.161] | 100.0% |
| UUID | 1 | 0.054 [-0.053, 0.138] | 0.002 [-0.002, 0.006] | 0.7% |
| UUID | 12 | -4.011 [-23.455, 15.264] | -0.557 [-1.280, 0.162] | -53.0% |
| UUID | 24 | 10.000 [1.847, 20.036] | 0.424 [0.083, 0.856] | 132.2% |
| UUID | 36 | 7.562 [0.794, 14.809] | 0.304 [0.019, 0.599] | 100.0% |

## Localization controls

| Identifier | Layer | Source-label endpoint | Relevant source content | Question endpoint control |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.027 [-0.086, 0.029] | -0.021 [-0.087, 0.049] | -0.040 [-0.115, 0.030] |
| [S1] | 12 | -0.056 [-0.166, 0.051] | 0.025 [-0.053, 0.115] | -0.036 [-0.096, 0.018] |
| [S1] | 24 | -0.027 [-0.077, 0.010] | -0.024 [-0.101, 0.042] | 0.012 [-0.039, 0.067] |
| [S1] | 36 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 1 | -0.034 [-0.155, 0.097] | -0.088 [-0.171, -0.001] | 0.004 [-0.081, 0.086] |
| [XQ7M] | 12 | -0.431 [-0.683, -0.183] | -0.237 [-0.523, 0.010] | -0.064 [-0.107, -0.011] |
| [XQ7M] | 24 | 0.076 [0.032, 0.127] | 0.013 [-0.032, 0.061] | 0.019 [-0.041, 0.075] |
| [XQ7M] | 36 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 1 | 0.048 [-0.010, 0.108] | 0.059 [-0.024, 0.128] | 0.066 [-0.006, 0.146] |
| UUID | 12 | -0.092 [-0.317, 0.108] | 0.032 [-0.148, 0.176] | 0.052 [-0.057, 0.155] |
| UUID | 24 | 0.021 [-0.046, 0.089] | 0.054 [-0.008, 0.113] | 0.034 [-0.038, 0.100] |
| UUID | 36 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

## Interpretation

1. **Binding follows the counterfactual label assignment.** Swapping only the identifier attached to a relevant source shifts the citation distribution toward that source's new label.
2. **The transferable citation state is late.** Early citation-context patches are near zero, whereas late output-region patches transfer most or all of the direct swap effect.
3. **A single source token is not the circuit.** Source-label endpoint and source-content patches are small relative to late citation-context patches, consistent with a distributed association that is converted into literal identifier tokens late in the network.
4. **UUID reconstruction is fragile.** UUID total effects aggregate many token predictions, and some intermediate patches are off-manifold outliers. Per-token effects, medians, early controls, and the final-layer recovery should be considered together.

## Checkpoint 7

**Decision: causal correct-rebinding evidence obtained.** This satisfies the roadmap gate for this model. Stage 6's representation-level signature is now paired with both a clean input intervention and activation-level transfer. It is not yet complete circuit discovery; the next mechanistic refinement is head/MLP-level patching within the late output region, followed by cross-model replication.

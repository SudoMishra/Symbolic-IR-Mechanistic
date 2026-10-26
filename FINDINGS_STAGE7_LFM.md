# Stage 7: causal source-to-identifier binding

**Design:** 8 semantic examples × 3 identifier formats = 24 paired source-ID swaps and 384 activation interventions on `LiquidAI/LFM2.5-1.2B-Instruct`. Prompts contain 2588–3850 tokens. The relevant source swaps identifiers with a distractor while source text, question, answer, and the identifier set remain fixed.

The primary direct effect is the change in `log P(swapped ID) - log P(original ID)` after the prompt swap. The patching effect is the same preference change after transplanting a state from the swapped run into the clean run. Intervals are 5,000-replicate paired bootstraps over semantic examples.

## Direct source-ID swap

| Identifier | Total log-probability effect | Per-token effect | Positive cases |
|---|---:|---:|---:|
| [S1] | -0.778 [-5.260, 3.881] | -0.194 [-1.335, 0.960] | 3/8 |
| [XQ7M] | -9.084 [-16.982, -1.004] | -2.058 [-3.840, -0.285] | 2/8 |
| UUID | -2.561 [-10.278, 6.822] | -0.125 [-0.453, 0.253] | 3/8 |

A positive value means the same semantic source becomes more likely to be cited with its new identifier after the swap. The prompt swap causally changes the citation distribution, but the average effect is not correct rebinding: the model tends to retain or strengthen preference for the source's original identifier.

## Citation-state activation patching

The citation-context intervention patches every residual state that predicts a token of the candidate identifier. Layer 1 is an early control; the other layers cover the Stage 6 binding/output regions.

| Identifier | Layer | Total patch effect | Per-token patch effect | Aggregate recovery |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.054 [-0.130, 0.014] | -0.014 [-0.031, 0.004] | 7.0% |
| [S1] | 6 | -0.228 [-0.365, -0.110] | -0.057 [-0.091, -0.027] | 29.4% |
| [S1] | 13 | -2.167 [-5.264, 1.361] | -0.542 [-1.317, 0.342] | 278.6% |
| [S1] | 16 | -0.744 [-5.278, 3.870] | -0.186 [-1.291, 0.995] | 95.7% |
| [XQ7M] | 1 | -0.041 [-0.097, 0.012] | -0.010 [-0.024, 0.001] | 0.5% |
| [XQ7M] | 6 | 0.263 [0.078, 0.450] | 0.057 [0.017, 0.097] | -2.9% |
| [XQ7M] | 13 | -2.546 [-5.351, 0.320] | -0.599 [-1.184, 0.005] | 28.0% |
| [XQ7M] | 16 | -9.009 [-17.221, -0.880] | -2.042 [-3.831, -0.290] | 99.2% |
| UUID | 1 | 0.017 [-0.013, 0.044] | 0.001 [-0.001, 0.002] | -0.7% |
| UUID | 6 | 1.278 [0.173, 3.215] | 0.050 [0.007, 0.120] | -49.9% |
| UUID | 13 | -0.035 [-1.479, 1.873] | -0.002 [-0.061, 0.075] | 1.4% |
| UUID | 16 | -2.585 [-10.180, 6.491] | -0.127 [-0.451, 0.261] | 100.9% |

## Localization controls

| Identifier | Layer | Source-label endpoint | Relevant source content | Question endpoint control |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.060 [-0.110, -0.009] | -0.069 [-0.143, 0.001] | -0.041 [-0.094, 0.020] |
| [S1] | 6 | -0.078 [-0.145, -0.009] | 0.559 [0.167, 0.972] | -0.071 [-0.109, -0.031] |
| [S1] | 13 | -0.000 [-0.003, 0.003] | -0.048 [-0.106, 0.015] | 0.002 [-0.001, 0.006] |
| [S1] | 16 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 1 | 0.041 [-0.080, 0.181] | -0.075 [-0.161, 0.022] | -0.018 [-0.073, 0.041] |
| [XQ7M] | 6 | -0.110 [-0.309, 0.099] | -0.215 [-0.773, 0.160] | -0.041 [-0.122, 0.037] |
| [XQ7M] | 13 | -0.003 [-0.056, 0.040] | -0.012 [-0.057, 0.040] | -0.011 [-0.058, 0.024] |
| [XQ7M] | 16 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 1 | -0.090 [-0.175, -0.024] | -0.033 [-0.091, 0.019] | -0.028 [-0.054, -0.007] |
| UUID | 6 | -0.009 [-0.082, 0.062] | 0.277 [0.206, 0.358] | 0.002 [-0.068, 0.070] |
| UUID | 13 | -0.015 [-0.037, 0.006] | -0.007 [-0.054, 0.034] | -0.005 [-0.030, 0.020] |
| UUID | 16 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

## Interpretation

1. **The model is causally sensitive but does not correctly rebind.** The identifier-only swap changes citation logits, yet the direction favors the old association on average.
2. **The transferable citation state is late.** Early citation-context patches are near zero, whereas late output-region patches transfer most or all of the direct swap effect.
3. **A single source token is not the circuit.** Source-label endpoint and source-content patches are small relative to late citation-context patches, consistent with a distributed association that is converted into literal identifier tokens late in the network.
4. **UUID reconstruction is fragile.** UUID total effects aggregate many token predictions, and some intermediate patches are off-manifold outliers. Per-token effects, medians, early controls, and the final-layer recovery should be considered together.

## Checkpoint 7

**Decision: causal sensitivity, but no correct-rebinding evidence for this model.** The causal protocol works, but this model is a mechanistic negative/control result rather than confirmation of the binding claim. Stage 6's representation-level signature is now paired with both a clean input intervention and activation-level transfer. It is not yet complete circuit discovery; the next mechanistic refinement is head/MLP-level patching within the late output region, followed by cross-model replication.

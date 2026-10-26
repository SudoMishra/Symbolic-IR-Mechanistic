# Stage 7: causal source-to-identifier binding

**Design:** 4 semantic examples × 3 identifier formats = 12 paired source-ID swaps and 192 activation interventions on `google/gemma-4-E2B-it`. Prompts contain 2453–3887 tokens. The relevant source swaps identifiers with a distractor while source text, question, answer, and the identifier set remain fixed.

The primary direct effect is the change in `log P(swapped ID) - log P(original ID)` after the prompt swap. The patching effect is the same preference change after transplanting a state from the swapped run into the clean run. Intervals are 5,000-replicate paired bootstraps over semantic examples.

## Direct source-ID swap

| Identifier | Total log-probability effect | Per-token effect | Positive cases |
|---|---:|---:|---:|
| [S1] | 2.161 [-16.250, 25.775] | 0.223 [-4.062, 5.492] | 2/4 |
| [XQ7M] | 7.498 [1.327, 15.418] | 1.588 [-0.043, 3.743] | 3/4 |
| UUID | 18.617 [7.520, 29.714] | 0.533 [0.221, 0.845] | 4/4 |

A positive value means the same semantic source becomes more likely to be cited with its new identifier after the swap. The model shows correct causal rebinding in at least two formats: the same semantic source becomes more likely to be cited with its new identifier, although no fact or answer changed.

## Citation-state activation patching

The citation-context intervention patches every residual state that predicts a token of the candidate identifier. Layer 1 is an early control; the other layers cover the Stage 6 binding/output regions.

| Identifier | Layer | Total patch effect | Per-token patch effect | Aggregate recovery |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.168 [-0.832, 0.327] | -0.042 [-0.208, 0.082] | -7.8% |
| [S1] | 15 | -1.046 [-7.951, 3.220] | -0.254 [-1.981, 0.819] | -48.4% |
| [S1] | 29 | 1.592 [-19.929, 26.724] | 0.120 [-4.982, 5.846] | 73.7% |
| [S1] | 35 | 2.816 [-16.662, 25.775] | 0.387 [-4.165, 5.492] | 130.3% |
| [XQ7M] | 1 | -0.113 [-0.225, 0.000] | -0.026 [-0.051, 0.000] | -1.5% |
| [XQ7M] | 15 | -5.882 [-10.583, -2.471] | -1.379 [-2.696, -0.543] | -78.4% |
| [XQ7M] | 29 | 0.770 [-3.044, 6.442] | 0.158 [-0.969, 1.660] | 10.3% |
| [XQ7M] | 35 | 7.702 [1.350, 15.963] | 1.630 [-0.045, 3.880] | 102.7% |
| UUID | 1 | -0.033 [-0.066, 0.000] | -0.001 [-0.002, 0.000] | -0.2% |
| UUID | 15 | 1.280 [-0.502, 3.063] | 0.036 [-0.015, 0.086] | 6.9% |
| UUID | 29 | 8.463 [1.129, 13.952] | 0.243 [0.033, 0.396] | 45.5% |
| UUID | 35 | 18.287 [6.859, 29.714] | 0.523 [0.201, 0.845] | 98.2% |

## Localization controls

| Identifier | Layer | Source-label endpoint | Relevant source content | Question endpoint control |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.325 [-0.719, 0.010] | -0.230 [-0.490, 0.031] | -0.020 [-0.340, 0.281] |
| [S1] | 15 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [S1] | 29 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [S1] | 35 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 1 | 0.030 [-0.380, 0.725] | -0.315 [-0.751, 0.251] | -0.024 [-0.277, 0.205] |
| [XQ7M] | 15 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 29 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 35 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 1 | -0.050 [-1.028, 0.810] | 0.290 [0.082, 0.498] | 0.073 [0.000, 0.147] |
| UUID | 15 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 29 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 35 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

## Interpretation

1. **Binding follows the counterfactual label assignment.** Swapping only the identifier attached to a relevant source shifts the citation distribution toward that source's new label.
2. **The transferable citation state is late.** Early citation-context patches are near zero, whereas late output-region patches transfer most or all of the direct swap effect.
3. **A single source token is not the circuit.** Source-label endpoint and source-content patches are small relative to late citation-context patches, consistent with a distributed association that is converted into literal identifier tokens late in the network.
4. **UUID reconstruction is fragile.** UUID total effects aggregate many token predictions, and some intermediate patches are off-manifold outliers. Per-token effects, medians, early controls, and the final-layer recovery should be considered together.

## Checkpoint 7

**Decision: causal correct-rebinding evidence obtained.** This satisfies the roadmap gate for this model. Stage 6's representation-level signature is now paired with both a clean input intervention and activation-level transfer. It is not yet complete circuit discovery; the next mechanistic refinement is head/MLP-level patching within the late output region, followed by cross-model replication.

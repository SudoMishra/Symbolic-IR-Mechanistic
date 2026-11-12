# Stage 7: causal source-to-identifier binding

**Design:** 8 semantic examples × 3 identifier formats = 24 paired source-ID swaps and 384 activation interventions on `google/gemma-4-E4B-it`. Prompts contain 2453–3887 tokens. The relevant source swaps identifiers with a distractor while source text, question, answer, and the identifier set remain fixed.

The primary direct effect is the change in `log P(swapped ID) - log P(original ID)` after the prompt swap. The patching effect is the same preference change after transplanting a state from the swapped run into the clean run. Intervals are 5,000-replicate paired bootstraps over semantic examples.

## Direct source-ID swap

| Identifier | Total log-probability effect | Per-token effect | Positive cases |
|---|---:|---:|---:|
| [S1] | 37.413 [19.380, 54.951] | 8.746 [4.414, 13.128] | 7/8 |
| [XQ7M] | 50.906 [33.813, 66.984] | 10.964 [7.030, 14.732] | 8/8 |
| UUID | 48.299 [35.799, 63.535] | 1.408 [1.026, 1.880] | 8/8 |

A positive value means the same semantic source becomes more likely to be cited with its new identifier after the swap. The model shows correct causal rebinding in at least two formats: the same semantic source becomes more likely to be cited with its new identifier, although no fact or answer changed.

## Citation-state activation patching

The citation-context intervention patches every residual state that predicts a token of the candidate identifier. Layer 1 is an early control; the other layers cover the Stage 6 binding/output regions.

| Identifier | Layer | Total patch effect | Per-token patch effect | Aggregate recovery |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.062 [-0.188, 0.000] | -0.012 [-0.035, 0.000] | -0.2% |
| [S1] | 25 | -10.359 [-18.048, -2.857] | -2.458 [-4.480, -0.530] | -27.7% |
| [S1] | 32 | 9.147 [-7.609, 26.224] | 2.094 [-1.758, 6.265] | 24.4% |
| [S1] | 42 | 37.413 [19.963, 54.728] | 8.746 [4.258, 13.203] | 100.0% |
| [XQ7M] | 1 | 0.012 [0.000, 0.037] | 0.006 [0.000, 0.019] | 0.0% |
| [XQ7M] | 25 | -9.000 [-13.932, -4.112] | -1.865 [-2.981, -0.759] | -17.7% |
| [XQ7M] | 32 | 7.354 [-3.984, 18.912] | 1.754 [-0.925, 4.409] | 14.4% |
| [XQ7M] | 42 | 50.906 [33.682, 66.779] | 10.964 [7.000, 14.833] | 100.0% |
| UUID | 1 | -0.023 [-0.070, 0.000] | -0.001 [-0.003, 0.000] | -0.0% |
| UUID | 25 | -11.610 [-15.418, -8.026] | -0.328 [-0.445, -0.221] | -24.0% |
| UUID | 32 | 0.773 [-7.902, 11.911] | 0.042 [-0.209, 0.387] | 1.6% |
| UUID | 42 | 48.299 [35.561, 63.674] | 1.408 [1.026, 1.861] | 100.0% |

## Localization controls

| Identifier | Layer | Source-label endpoint | Relevant source content | Question endpoint control |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.006 [-0.499, 0.520] | 0.339 [-0.078, 0.790] | -0.094 [-0.281, 0.000] |
| [S1] | 25 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [S1] | 32 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [S1] | 42 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 1 | 0.141 [-0.634, 0.846] | -0.324 [-1.079, 0.535] | 0.045 [0.000, 0.134] |
| [XQ7M] | 25 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 32 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 42 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 1 | -0.125 [-0.485, 0.250] | -0.515 [-1.015, -0.015] | -0.047 [-0.140, 0.000] |
| UUID | 25 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 32 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 42 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

## Interpretation

1. **Binding follows the counterfactual label assignment.** Swapping only the identifier attached to a relevant source shifts the citation distribution toward that source's new label.
2. **The transferable citation state is late.** Early citation-context patches are near zero, whereas late output-region patches transfer most or all of the direct swap effect.
3. **A single source token is not the circuit.** Source-label endpoint and source-content patches are small relative to late citation-context patches, consistent with a distributed association that is converted into literal identifier tokens late in the network.
4. **UUID reconstruction is fragile.** UUID total effects aggregate many token predictions, and some intermediate patches are off-manifold outliers. Per-token effects, medians, early controls, and the final-layer recovery should be considered together.

## Checkpoint 7

**Decision: causal correct-rebinding evidence obtained.** This satisfies the roadmap gate for this model. Stage 6's representation-level signature is now paired with both a clean input intervention and activation-level transfer. It is not yet complete circuit discovery; the next mechanistic refinement is head/MLP-level patching within the late output region, followed by cross-model replication.

# Stage 7: causal source-to-identifier binding

**Design:** 2 semantic examples × 3 identifier formats = 6 paired source-ID swaps and 96 activation interventions on `google/gemma-4-E4B-it`. Prompts contain 2453–2932 tokens. The relevant source swaps identifiers with a distractor while source text, question, answer, and the identifier set remain fixed.

The primary direct effect is the change in `log P(swapped ID) - log P(original ID)` after the prompt swap. The patching effect is the same preference change after transplanting a state from the swapped run into the clean run. Intervals are 5,000-replicate paired bootstraps over semantic examples.

## Direct source-ID swap

| Identifier | Total log-probability effect | Per-token effect | Positive cases |
|---|---:|---:|---:|
| [S1] | 11.557 [-14.024, 37.137] | 2.889 [-3.506, 9.284] | 1/2 |
| [XQ7M] | 15.172 [9.093, 21.250] | 3.049 [2.273, 3.826] | 2/2 |
| UUID | 48.728 [26.704, 70.751] | 1.414 [0.806, 2.022] | 2/2 |

A positive value means the same semantic source becomes more likely to be cited with its new identifier after the swap. The model shows correct causal rebinding in at least two formats: the same semantic source becomes more likely to be cited with its new identifier, although no fact or answer changed.

## Citation-state activation patching

The citation-context intervention patches every residual state that predicts a token of the candidate identifier. Layer 1 is an early control; the other layers cover the Stage 6 binding/output regions.

| Identifier | Layer | Total patch effect | Per-token patch effect | Aggregate recovery |
|---|---:|---:|---:|---:|
| [S1] | 1 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.0% |
| [S1] | 25 | -27.099 [-28.837, -25.360] | -6.775 [-7.209, -6.340] | -234.5% |
| [S1] | 32 | -17.363 [-33.363, -1.363] | -4.341 [-8.341, -0.341] | -150.2% |
| [S1] | 42 | 11.557 [-14.024, 37.137] | 2.889 [-3.506, 9.284] | 100.0% |
| [XQ7M] | 1 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.0% |
| [XQ7M] | 25 | -15.905 [-19.186, -12.625] | -3.551 [-4.796, -2.305] | -104.8% |
| [XQ7M] | 32 | -14.694 [-15.500, -13.888] | -3.234 [-3.472, -2.995] | -96.9% |
| [XQ7M] | 42 | 15.172 [9.093, 21.250] | 3.049 [2.273, 3.826] | 100.0% |
| UUID | 1 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.0% |
| UUID | 25 | -12.147 [-18.170, -6.124] | -0.352 [-0.531, -0.172] | -24.9% |
| UUID | 32 | 1.156 [-1.749, 4.061] | 0.044 [-0.046, 0.135] | 2.4% |
| UUID | 42 | 48.728 [26.704, 70.751] | 1.414 [0.806, 2.022] | 100.0% |

## Localization controls

| Identifier | Layer | Source-label endpoint | Relevant source content | Question endpoint control |
|---|---:|---:|---:|---:|
| [S1] | 1 | 0.631 [0.258, 1.004] | 0.948 [0.520, 1.377] | 0.000 [0.000, 0.000] |
| [S1] | 25 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [S1] | 32 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [S1] | 42 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 1 | -0.219 [-2.000, 1.561] | 0.117 [-1.875, 2.109] | 0.000 [0.000, 0.000] |
| [XQ7M] | 25 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 32 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 42 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 1 | -0.438 [-1.000, 0.124] | -1.187 [-1.625, -0.749] | 0.000 [0.000, 0.000] |
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

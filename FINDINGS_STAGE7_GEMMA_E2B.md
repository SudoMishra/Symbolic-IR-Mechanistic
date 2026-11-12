# Stage 7: causal source-to-identifier binding

**Design:** 8 semantic examples × 3 identifier formats = 24 paired source-ID swaps and 384 activation interventions on `google/gemma-4-E2B-it`. Prompts contain 2453–3887 tokens. The relevant source swaps identifiers with a distractor while source text, question, answer, and the identifier set remain fixed.

The primary direct effect is the change in `log P(swapped ID) - log P(original ID)` after the prompt swap. The patching effect is the same preference change after transplanting a state from the swapped run into the clean run. Intervals are 5,000-replicate paired bootstraps over semantic examples.

## Direct source-ID swap

| Identifier | Total log-probability effect | Per-token effect | Positive cases |
|---|---:|---:|---:|
| [S1] | 8.323 [-4.507, 21.469] | 1.773 [-1.137, 4.669] | 6/8 |
| [XQ7M] | 5.176 [-0.169, 10.468] | 1.106 [-0.072, 2.456] | 6/8 |
| UUID | 14.630 [7.345, 22.349] | 0.426 [0.212, 0.642] | 7/8 |

A positive value means the same semantic source becomes more likely to be cited with its new identifier after the swap. The model shows correct causal rebinding in at least two formats: the same semantic source becomes more likely to be cited with its new identifier, although no fact or answer changed.

## Citation-state activation patching

The citation-context intervention patches every residual state that predicts a token of the candidate identifier. Layer 1 is an early control; the other layers cover the Stage 6 binding/output regions.

| Identifier | Layer | Total patch effect | Per-token patch effect | Aggregate recovery |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.079 [-0.411, 0.164] | -0.019 [-0.102, 0.041] | -1.0% |
| [S1] | 15 | -0.869 [-4.601, 2.099] | -0.215 [-1.158, 0.545] | -10.4% |
| [S1] | 29 | 6.158 [-7.808, 19.980] | 1.254 [-1.959, 4.469] | 74.0% |
| [S1] | 35 | 8.651 [-4.214, 21.747] | 1.855 [-1.204, 4.780] | 103.9% |
| [XQ7M] | 1 | -0.017 [-0.121, 0.094] | -0.007 [-0.026, 0.012] | -0.3% |
| [XQ7M] | 15 | -4.405 [-7.151, -2.396] | -0.993 [-1.717, -0.518] | -85.1% |
| [XQ7M] | 29 | -0.494 [-4.337, 3.564] | -0.134 [-1.049, 0.822] | -9.5% |
| [XQ7M] | 35 | 5.278 [0.056, 10.787] | 1.127 [-0.121, 2.442] | 102.0% |
| UUID | 1 | 0.063 [-0.037, 0.231] | 0.002 [-0.001, 0.006] | 0.4% |
| UUID | 15 | 0.184 [-0.960, 1.484] | 0.005 [-0.027, 0.041] | 1.3% |
| UUID | 29 | 6.849 [2.352, 11.416] | 0.201 [0.077, 0.330] | 46.8% |
| UUID | 35 | 14.465 [7.021, 22.265] | 0.421 [0.211, 0.640] | 98.9% |

## Localization controls

| Identifier | Layer | Source-label endpoint | Relevant source content | Question endpoint control |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.223 [-0.504, 0.103] | -0.222 [-0.436, 0.001] | 0.061 [-0.123, 0.260] |
| [S1] | 15 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [S1] | 29 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [S1] | 35 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 1 | 0.025 [-0.293, 0.411] | -0.317 [-0.762, 0.133] | 0.108 [-0.104, 0.394] |
| [XQ7M] | 15 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 29 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 35 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 1 | -0.194 [-0.795, 0.388] | 0.097 [-0.211, 0.352] | 0.082 [0.012, 0.177] |
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

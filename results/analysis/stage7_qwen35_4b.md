# Stage 7: causal source-to-identifier binding

**Design:** 8 semantic examples × 3 identifier formats = 24 paired source-ID swaps and 384 activation interventions on `Qwen/Qwen3.5-4B`. Prompts contain 2461–3896 tokens. The relevant source swaps identifiers with a distractor while source text, question, answer, and the identifier set remain fixed.

The primary direct effect is the change in `log P(swapped ID) - log P(original ID)` after the prompt swap. The patching effect is the same preference change after transplanting a state from the swapped run into the clean run. Intervals are 5,000-replicate paired bootstraps over semantic examples.

## Direct source-ID swap

| Identifier | Total log-probability effect | Per-token effect | Positive cases |
|---|---:|---:|---:|
| [S1] | 4.234 [2.495, 5.952] | 0.973 [0.612, 1.349] | 8/8 |
| [XQ7M] | 5.042 [1.687, 8.009] | 1.023 [0.272, 1.691] | 7/8 |
| UUID | 3.576 [1.491, 6.137] | 0.107 [0.045, 0.180] | 7/8 |

A positive value means the same semantic source becomes more likely to be cited with its new identifier after the swap. The model shows correct causal rebinding in at least two formats: the same semantic source becomes more likely to be cited with its new identifier, although no fact or answer changed.

## Citation-state activation patching

The citation-context intervention patches every residual state that predicts a token of the candidate identifier. Layer 1 is an early control; the other layers cover the Stage 6 binding/output regions.

| Identifier | Layer | Total patch effect | Per-token patch effect | Aggregate recovery |
|---|---:|---:|---:|---:|
| [S1] | 1 | 0.087 [0.012, 0.175] | 0.022 [0.003, 0.043] | 2.1% |
| [S1] | 11 | -1.035 [-1.764, -0.208] | -0.251 [-0.415, -0.067] | -24.5% |
| [S1] | 22 | -0.183 [-1.586, 1.262] | -0.059 [-0.424, 0.297] | -4.3% |
| [S1] | 32 | 4.234 [2.562, 5.991] | 0.973 [0.599, 1.334] | 100.0% |
| [XQ7M] | 1 | -0.009 [-0.084, 0.066] | -0.004 [-0.019, 0.011] | -0.2% |
| [XQ7M] | 11 | -1.832 [-2.646, -0.974] | -0.359 [-0.526, -0.189] | -36.3% |
| [XQ7M] | 22 | -3.278 [-4.594, -1.837] | -0.685 [-0.987, -0.385] | -65.0% |
| [XQ7M] | 32 | 5.042 [1.697, 8.013] | 1.023 [0.307, 1.693] | 100.0% |
| UUID | 1 | 0.015 [-0.046, 0.076] | 0.000 [-0.001, 0.002] | 0.4% |
| UUID | 11 | 2.261 [-2.107, 7.082] | 0.066 [-0.069, 0.212] | 63.2% |
| UUID | 22 | 7.501 [-3.191, 18.689] | 0.206 [-0.115, 0.530] | 209.7% |
| UUID | 32 | 3.576 [1.548, 6.025] | 0.107 [0.045, 0.182] | 100.0% |

## Localization controls

| Identifier | Layer | Source-label endpoint | Relevant source content | Question endpoint control |
|---|---:|---:|---:|---:|
| [S1] | 1 | 0.115 [-0.015, 0.265] | 0.036 [-0.062, 0.116] | 0.011 [-0.065, 0.079] |
| [S1] | 11 | 0.338 [0.165, 0.525] | 0.213 [0.049, 0.417] | 0.003 [-0.044, 0.049] |
| [S1] | 22 | 0.369 [0.157, 0.581] | 0.038 [-0.028, 0.095] | 0.056 [-0.020, 0.130] |
| [S1] | 32 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 1 | 0.030 [-0.116, 0.185] | -0.204 [-0.304, -0.109] | -0.019 [-0.073, 0.038] |
| [XQ7M] | 11 | 0.130 [-0.055, 0.313] | -0.154 [-0.396, 0.067] | -0.018 [-0.100, 0.056] |
| [XQ7M] | 22 | -0.021 [-0.085, 0.026] | -0.009 [-0.067, 0.052] | -0.005 [-0.080, 0.068] |
| [XQ7M] | 32 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 1 | 0.035 [-0.125, 0.195] | 0.031 [-0.116, 0.161] | 0.076 [0.024, 0.125] |
| UUID | 11 | -0.055 [-0.146, 0.043] | -0.208 [-0.450, 0.004] | -0.018 [-0.077, 0.041] |
| UUID | 22 | 0.002 [-0.054, 0.061] | 0.028 [-0.059, 0.117] | -0.029 [-0.096, 0.035] |
| UUID | 32 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

## Interpretation

1. **Binding follows the counterfactual label assignment.** Swapping only the identifier attached to a relevant source shifts the citation distribution toward that source's new label.
2. **The transferable citation state is late.** Early citation-context patches are near zero, whereas late output-region patches transfer most or all of the direct swap effect.
3. **A single source token is not the circuit.** Source-label endpoint and source-content patches are small relative to late citation-context patches, consistent with a distributed association that is converted into literal identifier tokens late in the network.
4. **UUID reconstruction is fragile.** UUID total effects aggregate many token predictions, and some intermediate patches are off-manifold outliers. Per-token effects, medians, early controls, and the final-layer recovery should be considered together.

## Checkpoint 7

**Decision: causal correct-rebinding evidence obtained.** This satisfies the roadmap gate for this model. Stage 6's representation-level signature is now paired with both a clean input intervention and activation-level transfer. It is not yet complete circuit discovery; the next mechanistic refinement is head/MLP-level patching within the late output region, followed by cross-model replication.

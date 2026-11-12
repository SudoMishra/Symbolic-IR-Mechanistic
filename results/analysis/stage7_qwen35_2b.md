# Stage 7: causal source-to-identifier binding

**Design:** 8 semantic examples × 3 identifier formats = 24 paired source-ID swaps and 384 activation interventions on `Qwen/Qwen3.5-2B`. Prompts contain 2461–3896 tokens. The relevant source swaps identifiers with a distractor while source text, question, answer, and the identifier set remain fixed.

The primary direct effect is the change in `log P(swapped ID) - log P(original ID)` after the prompt swap. The patching effect is the same preference change after transplanting a state from the swapped run into the clean run. Intervals are 5,000-replicate paired bootstraps over semantic examples.

## Direct source-ID swap

| Identifier | Total log-probability effect | Per-token effect | Positive cases |
|---|---:|---:|---:|
| [S1] | 1.912 [0.891, 3.194] | 0.455 [0.214, 0.773] | 8/8 |
| [XQ7M] | 6.203 [1.873, 10.961] | 1.379 [0.399, 2.420] | 6/8 |
| UUID | 4.673 [2.524, 6.525] | 0.142 [0.078, 0.200] | 7/8 |

A positive value means the same semantic source becomes more likely to be cited with its new identifier after the swap. The model shows correct causal rebinding in at least two formats: the same semantic source becomes more likely to be cited with its new identifier, although no fact or answer changed.

## Citation-state activation patching

The citation-context intervention patches every residual state that predicts a token of the candidate identifier. Layer 1 is an early control; the other layers cover the Stage 6 binding/output regions.

| Identifier | Layer | Total patch effect | Per-token patch effect | Aggregate recovery |
|---|---:|---:|---:|---:|
| [S1] | 1 | 0.051 [-0.021, 0.151] | 0.011 [-0.008, 0.035] | 2.7% |
| [S1] | 8 | 1.096 [0.511, 1.694] | 0.258 [0.126, 0.392] | 57.3% |
| [S1] | 16 | 2.038 [0.946, 3.266] | 0.475 [0.221, 0.769] | 106.6% |
| [S1] | 24 | 1.912 [0.910, 3.227] | 0.455 [0.205, 0.773] | 100.0% |
| [XQ7M] | 1 | -0.041 [-0.135, 0.045] | -0.011 [-0.035, 0.008] | -0.7% |
| [XQ7M] | 8 | 1.209 [0.247, 2.315] | 0.270 [0.069, 0.504] | 19.5% |
| [XQ7M] | 16 | 2.868 [0.334, 6.047] | 0.584 [0.047, 1.198] | 46.2% |
| [XQ7M] | 24 | 6.203 [1.873, 11.064] | 1.379 [0.390, 2.441] | 100.0% |
| UUID | 1 | -0.008 [-0.073, 0.049] | -0.000 [-0.002, 0.002] | -0.2% |
| UUID | 8 | 7.728 [1.844, 15.436] | 0.230 [0.055, 0.464] | 165.4% |
| UUID | 16 | 1.924 [-0.152, 3.806] | 0.053 [-0.008, 0.112] | 41.2% |
| UUID | 24 | 4.673 [2.521, 6.683] | 0.142 [0.079, 0.201] | 100.0% |

## Localization controls

| Identifier | Layer | Source-label endpoint | Relevant source content | Question endpoint control |
|---|---:|---:|---:|---:|
| [S1] | 1 | 0.011 [-0.089, 0.098] | 0.076 [0.010, 0.139] | 0.035 [-0.033, 0.110] |
| [S1] | 8 | 0.254 [0.034, 0.516] | 0.220 [0.057, 0.391] | 0.066 [0.001, 0.131] |
| [S1] | 16 | 0.277 [0.119, 0.440] | 0.047 [0.003, 0.105] | 0.006 [-0.047, 0.060] |
| [S1] | 24 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 1 | -0.018 [-0.118, 0.064] | -0.026 [-0.090, 0.036] | 0.009 [-0.080, 0.083] |
| [XQ7M] | 8 | 0.426 [0.095, 0.784] | 0.131 [-0.089, 0.336] | -0.006 [-0.059, 0.052] |
| [XQ7M] | 16 | 0.095 [-0.008, 0.202] | 0.018 [-0.095, 0.118] | 0.007 [-0.050, 0.058] |
| [XQ7M] | 24 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 1 | -0.132 [-0.231, -0.041] | -0.028 [-0.096, 0.045] | -0.008 [-0.069, 0.060] |
| UUID | 8 | 0.190 [-0.122, 0.578] | -0.053 [-0.121, 0.028] | -0.039 [-0.120, 0.067] |
| UUID | 16 | -0.006 [-0.064, 0.054] | -0.070 [-0.147, 0.008] | -0.011 [-0.051, 0.028] |
| UUID | 24 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

## Interpretation

1. **Binding follows the counterfactual label assignment.** Swapping only the identifier attached to a relevant source shifts the citation distribution toward that source's new label.
2. **The transferable citation state is late.** Early citation-context patches are near zero, whereas late output-region patches transfer most or all of the direct swap effect.
3. **A single source token is not the circuit.** Source-label endpoint and source-content patches are small relative to late citation-context patches, consistent with a distributed association that is converted into literal identifier tokens late in the network.
4. **UUID reconstruction is fragile.** UUID total effects aggregate many token predictions, and some intermediate patches are off-manifold outliers. Per-token effects, medians, early controls, and the final-layer recovery should be considered together.

## Checkpoint 7

**Decision: causal correct-rebinding evidence obtained.** This satisfies the roadmap gate for this model. Stage 6's representation-level signature is now paired with both a clean input intervention and activation-level transfer. It is not yet complete circuit discovery; the next mechanistic refinement is head/MLP-level patching within the late output region, followed by cross-model replication.

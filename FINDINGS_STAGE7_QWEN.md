# Stage 7: causal source-to-identifier binding

**Design:** 8 semantic examples × 3 identifier formats = 24 paired source-ID swaps and 384 activation interventions on `Qwen/Qwen2.5-1.5B-Instruct`. Prompts contain 2452–3889 tokens. The relevant source swaps identifiers with a distractor while source text, question, answer, and the identifier set remain fixed.

The primary direct effect is the change in `log P(swapped ID) - log P(original ID)` after the prompt swap. The patching effect is the same preference change after transplanting a state from the swapped run into the clean run. Intervals are 5,000-replicate paired bootstraps over semantic examples.

## Direct source-ID swap

| Identifier | Total log-probability effect | Per-token effect | Positive cases |
|---|---:|---:|---:|
| [S1] | 2.635 [0.781, 4.351] | 0.643 [0.204, 1.061] | 6/8 |
| [XQ7M] | 4.978 [2.450, 7.438] | 1.062 [0.518, 1.578] | 7/8 |
| UUID | 1.905 [-1.319, 4.928] | 0.056 [-0.041, 0.150] | 5/8 |

A positive value means the same semantic source becomes more likely to be cited with its new identifier after the swap. The model shows correct causal rebinding in at least two formats: the same semantic source becomes more likely to be cited with its new identifier, although no fact or answer changed.

## Citation-state activation patching

The citation-context intervention patches every residual state that predicts a token of the candidate identifier. Layer 1 is an early control; the other layers cover the Stage 6 binding/output regions.

| Identifier | Layer | Total patch effect | Per-token patch effect | Aggregate recovery |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.025 [-0.129, 0.071] | -0.006 [-0.031, 0.017] | -0.9% |
| [S1] | 12 | 0.152 [-0.043, 0.405] | 0.032 [-0.011, 0.085] | 5.8% |
| [S1] | 24 | 2.856 [1.171, 4.460] | 0.690 [0.301, 1.079] | 108.4% |
| [S1] | 28 | 2.611 [0.657, 4.444] | 0.638 [0.200, 1.074] | 99.1% |
| [XQ7M] | 1 | 0.015 [-0.073, 0.107] | 0.004 [-0.014, 0.023] | 0.3% |
| [XQ7M] | 12 | 0.653 [-0.223, 2.113] | 0.126 [-0.052, 0.429] | 13.1% |
| [XQ7M] | 24 | 3.658 [2.995, 4.392] | 0.758 [0.619, 0.909] | 73.5% |
| [XQ7M] | 28 | 4.965 [2.353, 7.508] | 1.063 [0.495, 1.641] | 99.7% |
| UUID | 1 | -0.044 [-0.121, 0.044] | -0.001 [-0.004, 0.001] | -2.3% |
| UUID | 12 | 20.814 [0.122, 51.182] | 0.587 [0.003, 1.400] | 1092.8% |
| UUID | 24 | 1.756 [-0.901, 4.183] | 0.052 [-0.031, 0.124] | 92.2% |
| UUID | 28 | 1.884 [-1.261, 5.003] | 0.055 [-0.043, 0.152] | 98.9% |

## Localization controls

| Identifier | Layer | Source-label endpoint | Relevant source content | Question endpoint control |
|---|---:|---:|---:|---:|
| [S1] | 1 | -0.019 [-0.089, 0.042] | 0.059 [-0.024, 0.138] | -0.026 [-0.089, 0.045] |
| [S1] | 12 | 0.326 [0.137, 0.513] | 0.168 [0.017, 0.347] | 0.036 [-0.002, 0.082] |
| [S1] | 24 | 0.021 [-0.077, 0.121] | -0.029 [-0.113, 0.049] | 0.009 [-0.057, 0.072] |
| [S1] | 28 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| [XQ7M] | 1 | -0.015 [-0.152, 0.112] | 0.004 [-0.072, 0.077] | -0.047 [-0.114, 0.017] |
| [XQ7M] | 12 | 0.127 [-0.049, 0.324] | 0.080 [-0.056, 0.233] | -0.041 [-0.129, 0.041] |
| [XQ7M] | 24 | -0.014 [-0.072, 0.047] | -0.011 [-0.044, 0.017] | 0.030 [-0.024, 0.102] |
| [XQ7M] | 28 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| UUID | 1 | -0.077 [-0.132, -0.010] | 0.005 [-0.103, 0.133] | -0.080 [-0.157, -0.017] |
| UUID | 12 | -0.093 [-0.196, -0.001] | 0.056 [-0.027, 0.133] | -0.038 [-0.099, 0.031] |
| UUID | 24 | -0.025 [-0.103, 0.052] | -0.021 [-0.084, 0.045] | 0.043 [-0.017, 0.095] |
| UUID | 28 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

## Interpretation

1. **Binding follows the counterfactual label assignment.** Swapping only the identifier attached to a relevant source shifts the citation distribution toward that source's new label.
2. **The transferable citation state is late.** Early citation-context patches are near zero, whereas late output-region patches transfer most or all of the direct swap effect.
3. **A single source token is not the circuit.** Source-label endpoint and source-content patches are small relative to late citation-context patches, consistent with a distributed association that is converted into literal identifier tokens late in the network.
4. **UUID reconstruction is fragile.** UUID total effects aggregate many token predictions, and some intermediate patches are off-manifold outliers. Per-token effects, medians, early controls, and the final-layer recovery should be considered together.

## Checkpoint 7

**Decision: causal correct-rebinding evidence obtained.** This satisfies the roadmap gate for this model. Stage 6's representation-level signature is now paired with both a clean input intervention and activation-level transfer. It is not yet complete circuit discovery; the next mechanistic refinement is head/MLP-level patching within the late output region, followed by cross-model replication.

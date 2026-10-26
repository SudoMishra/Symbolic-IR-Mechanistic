# Stage 7 cross-model causal synthesis

The intervention swaps the identifiers assigned to one relevant source and one distractor while holding source text, identifier set, question, and answer fixed. Positive direct effects mean the model follows the relevant source to its newly assigned identifier.

Cohort sizes differ because Gemma uses CPU offload on the 8 GiB GPU: Qwen and LFM use 8 semantic examples, Gemma E2B uses 4, and Gemma E4B is a 2-example diagnostic. Gemma intervals are therefore pilot-level and E4B is descriptive only.

## Direct counterfactual rebinding

| Model | n | [S1] swap effect | [XQ7M] swap effect | UUID swap effect | Decision |
|---|---:|---:|---:|---:|---|
| Qwen 1.5B | 8 | 2.63 [0.78, 4.35] | 4.98 [2.45, 7.44] | 1.90 [-1.32, 4.93] | correct rebinding |
| LFM 1.2B | 8 | -0.78 [-5.26, 3.88] | -9.08 [-16.98, -1.00] | -2.56 [-10.28, 6.82] | sensitive, inverted/old binding |
| Gemma E2B | 4 | 2.16 [-16.25, 25.78] | 7.50 [1.33, 15.42] | 18.62 [7.52, 29.71] | correct rebinding |
| Gemma E4B | 2 | 11.56 [-14.02, 37.14] | 15.17 [9.09, 21.25] | 48.73 [26.70, 70.75] | correct rebinding |

## Where the counterfactual citation state becomes transferable

Recovery is the patch effect divided by the model's own direct swap effect. The penultimate sampled layer is the Stage 6 late-output candidate; the final layer is a positive-control transplant of the fully formed citation state.

| Model | Sampled late layer | [S1] recovery | [XQ7M] recovery | UUID recovery | Final-layer recovery range |
|---|---:|---:|---:|---:|---:|
| Qwen 1.5B | 24 | 108% | 73% | 92% | 99%–100% |
| LFM 1.2B | 13 | 279% | 28% | 1% | 96%–101% |
| Gemma E2B | 29 | 74% | 10% | 45% | 98%–130% |
| Gemma E4B | 32 | -150% | -97% | 2% | 100%–100% |

## Findings

1. **The causal binding claim is model-dependent.** Qwen and both Gemma pilots follow the semantic source to its new identifier. LFM changes its citation distribution but, on average, favors the old association; compact IDs are significantly inverted.
2. **Exact identifier reconstruction is late in every model.** Final-layer citation-state patches transfer approximately the full prompt-swap effect, while early controls are near zero.
3. **The onset differs substantially.** Qwen has already transferred 74–108% at layer 24. Gemma E2B shows partial UUID transfer at layer 29. Gemma E4B's sampled layer 32 does not yet carry the short-ID effect in the correct direction, and its UUID effect is only 2%, placing reconstruction very late.
4. **Source-local endpoint patches are not sufficient.** Across models, patching one label endpoint or one relevant fact span is much smaller and less consistent than patching the citation-generation trajectory. The source→identifier association is therefore not localized to the sampled endpoint alone.
5. **Stage 6's shared geometry does not imply shared causal behavior.** All four models passed the representation gate, yet LFM fails correct counterfactual rebinding and the Gemma/Qwen output timelines differ. That dissociation is the central Stage 7 result.

## Next mechanistic step

Run component-level patching in the model-specific transition region, not at a common normalized depth:

- Qwen: attention and MLP outputs in layers 20–24;
- LFM: layers 6–13, treating it as an inverted-binding control;
- Gemma E2B: layers 29–35;
- Gemma E4B: densely sample layers 33–42 before head/MLP decomposition.

Use a larger independent Stage 7 cohort before making population-level claims for either Gemma model.

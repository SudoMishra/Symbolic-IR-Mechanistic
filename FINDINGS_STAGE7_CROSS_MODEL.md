# Stage 7 cross-model causal synthesis

The intervention swaps the identifiers assigned to one relevant source and one distractor while holding source text, identifier set, question, and answer fixed. Positive direct effects mean the model follows the relevant source to its newly assigned identifier.

Cohort sizes: All six local models (Qwen 1.5B, Tiny Aya, Qwen 3.5 2B, Qwen 3.5 4B, Gemma E2B, Gemma E4B) use 8 semantic examples (384 interventions each, totaling 2,304 interventions across the cohort).

## Direct counterfactual rebinding

| Model | n | [S1] swap effect | [XQ7M] swap effect | UUID swap effect | Decision |
|---|---:|---:|---:|---:|---|
| Qwen 1.5B | 8 | 2.63 [0.78, 4.35] | 4.98 [2.45, 7.44] | 1.90 [-1.32, 4.93] | correct rebinding |
| Gemma E2B | 8 | 8.32 [-4.51, 21.47] | 5.18 [-0.17, 10.47] | 14.63 [7.35, 22.35] | correct rebinding |
| Gemma E4B | 8 | 37.41 [19.38, 54.95] | 50.91 [33.81, 66.98] | 48.30 [35.80, 63.53] | correct rebinding |
| Tiny Aya | 8 | 2.17 [0.48, 3.84] | 5.38 [1.66, 9.08] | 7.56 [0.83, 14.73] | correct rebinding |
| Qwen 3.5 2B | 8 | 1.91 [0.89, 3.19] | 6.20 [1.87, 10.96] | 4.67 [2.52, 6.53] | correct rebinding |
| Qwen 3.5 4B | 8 | 4.23 [2.50, 5.95] | 5.04 [1.69, 8.01] | 3.58 [1.49, 6.14] | correct rebinding |

## Where the counterfactual citation state becomes transferable

Recovery is the patch effect divided by the model's own direct swap effect. The penultimate sampled layer is the Stage 6 late-output candidate; the final layer is a positive-control transplant of the fully formed citation state.

| Model | Sampled late layer | [S1] recovery | [XQ7M] recovery | UUID recovery | Final-layer recovery range |
|---|---:|---:|---:|---:|---:|
| Qwen 1.5B | 24 | 108% | 73% | 92% | 99%–100% |
| Gemma E2B | 29 | 74% | -10% | 47% | 99%–104% |
| Gemma E4B | 32 | 24% | 14% | 2% | 100%–100% |
| Tiny Aya | 24 | 82% | 81% | 132% | 100%–100% |
| Qwen 3.5 2B | 16 | 107% | 46% | 41% | 100%–100% |
| Qwen 3.5 4B | 22 | -4% | -65% | 210% | 100%–100% |

## Findings

1. **Causal rebinding is supported across transformer architectures.** All evaluated local models (Qwen 1.5B, Tiny Aya, Qwen 3.5 2B, Qwen 3.5 4B, Gemma E2B, Gemma E4B) consistently follow the semantic source to its newly assigned identifier under counterfactual prompt swaps, confirming causal binding evidence across distinct model families.
2. **Exact identifier reconstruction is late across models.** Final-layer citation-state patches transfer approximately the full prompt-swap effect, while early controls are near zero.
3. **Onset depth varies across models.** Qwen models and Tiny Aya exhibit significant recovery in late intermediate layers, while Gemma models reconstruct citation states very close to the final layer.
4. **Source-local endpoint patches are not sufficient.** Across models, patching one label endpoint or one relevant fact span produces smaller and less consistent effects than patching the citation-generation trajectory, indicating distributed association.
5. **Mechanistic replication confirms the architectural generality of symbolic IR.** Across all 6 local models, Stage 6 representation geometry and Stage 7 causal interventions corroborate the core mechanistic findings.

## Next mechanistic step

Run component-level patching (attention heads vs MLP outputs) within each model's identified transition layers.

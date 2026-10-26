# Stage 6 cross-model replication

All models use the same 80 semantic examples and three paired identifier formats. States are teacher-forced and span-aligned; likelihood deltas are UUID minus structured.

The operational representation gate requires minimum source-fact CKA ≥0.90, a source-label CKA gain of at least 0.10 over the embedding layer, and a final-layer question-minus-pre-citation cosine gap of at least 0.05.

| Model | Blocks | Label CKA L0 → peak (layer) | Min fact CKA | Final question / pre-citation / citation cosine | Answer NLL Δ | Citation total NLL Δ | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Qwen | 28 | 0.325 → 0.858 (L13) | 0.969 | 0.999 / 0.828 / 0.721 | +0.011 [-0.119, +0.139] | -2.045 [-3.115, -0.949] | proceed_to_targeted_stage7 |
| LFM | 16 | 0.697 → 0.895 (L6) | 0.970 | 0.983 / 0.598 / 0.372 | +0.270 [-0.032, +0.590] | +1.930 [+0.668, +3.147] | proceed_to_targeted_stage7 |
| Gemma E2B | 35 | 0.434 → 0.931 (L15) | 0.941 | 0.994 / 0.825 / 0.798 | +0.656 [+0.208, +1.137] | +0.451 [-3.887, +4.665] | proceed_to_targeted_stage7 |
| Gemma E4B | 42 | 0.435 → 0.952 (L25) | 0.979 | 0.991 / 0.497 / 0.512 | -0.072 [-0.643, +0.529] | -11.325 [-15.573, -7.279] | proceed_to_targeted_stage7 |

## Synthesis

The roadmap's geometric signature passed the automated gate in 4/4 models: Qwen, LFM, Gemma E2B, Gemma E4B. Across those models, source-fact geometry remains largely format-invariant while source-label geometry converges after lexically different embeddings and citation states become more format-specific late in the stack.

A statistically positive UUID answer-NLL penalty appears in Gemma E2B. A positive total citation-NLL penalty appears in LFM, while a negative total citation-NLL effect appears in Qwen, Gemma E4B. The shared representation pattern alongside heterogeneous likelihood costs argues against one universal literal-copying explanation; Stage 7 should test whether causal binding interventions transfer across models.

## Stage 7 intervention targets

| Model | Candidate binding layers | Late output comparison layers |
|---|---|---|
| Qwen | 10–14 | 20–28 |
| LFM | 4–8 | 11–16 |
| Gemma E2B | 13–17 | 24–35 |
| Gemma E4B | 23–27 | 29–42 |

Tiny Aya is not included because its official Transformers checkpoint is gated and this host is not authenticated. The local GGUF artifact supports behavioral generation but does not expose per-layer residual states, so substituting it would not be the same Stage 6 experiment.

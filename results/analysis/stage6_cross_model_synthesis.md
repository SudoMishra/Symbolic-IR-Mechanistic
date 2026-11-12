# Stage 6 cross-model replication

All models use the same 80 semantic examples and three paired identifier formats. States are teacher-forced and span-aligned; likelihood deltas are UUID minus structured.

The operational representation gate requires minimum source-fact CKA ≥0.90, a source-label CKA gain of at least 0.10 over the embedding layer, and a final-layer question-minus-pre-citation cosine gap of at least 0.05.

| Model | Blocks | Label CKA L0 → peak (layer) | Min fact CKA | Final question / pre-citation / citation cosine | Answer NLL Δ | Citation total NLL Δ | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Qwen 1.5B | 28 | 0.325 → 0.858 (L13) | 0.969 | 0.999 / 0.828 / 0.721 | +0.011 [-0.119, +0.139] | -2.045 [-3.115, -0.949] | proceed_to_targeted_stage7 |
| Gemma E2B | 35 | 0.434 → 0.931 (L15) | 0.941 | 0.994 / 0.825 / 0.798 | +0.656 [+0.208, +1.137] | +0.451 [-3.887, +4.665] | proceed_to_targeted_stage7 |
| Gemma E4B | 42 | 0.435 → 0.952 (L25) | 0.979 | 0.991 / 0.497 / 0.512 | -0.072 [-0.643, +0.529] | -11.325 [-15.573, -7.279] | proceed_to_targeted_stage7 |
| Tiny Aya | 36 | 0.413 → 0.915 (L12) | 0.610 | 0.990 / 0.435 / 0.447 | -0.275 [-0.445, -0.118] | +4.254 [+3.299, +5.258] | no_clear_stage7_gate |
| Qwen 3.5 2B | 24 | 0.316 → 0.908 (L16) | 0.985 | 0.998 / 0.779 / 0.586 | -0.024 [-0.083, +0.028] | +0.899 [+0.190, +1.628] | proceed_to_targeted_stage7 |
| Qwen 3.5 4B | 32 | 0.330 → 0.919 (L17) | 0.984 | 0.998 / 0.733 / 0.606 | -0.097 [-0.170, -0.027] | +0.126 [-0.340, +0.610] | proceed_to_targeted_stage7 |

## Synthesis

The roadmap's geometric signature passed the automated gate in 5/6 models: Qwen 1.5B, Gemma E2B, Gemma E4B, Qwen 3.5 2B, Qwen 3.5 4B. Across those models, source-fact geometry remains largely format-invariant while source-label geometry converges after lexically different embeddings and citation states become more format-specific late in the stack.

A statistically positive UUID answer-NLL penalty appears in Gemma E2B. A positive total citation-NLL penalty appears in Tiny Aya, Qwen 3.5 2B, while a negative total citation-NLL effect appears in Qwen 1.5B, Gemma E4B. The shared representation pattern alongside heterogeneous likelihood costs argues against one universal literal-copying explanation; Stage 7 should test whether causal binding interventions transfer across models.

## Stage 7 intervention targets

| Model | Candidate binding layers | Late output comparison layers |
|---|---|---|
| Qwen 1.5B | 10–14 | 20–28 |
| Gemma E2B | 13–17 | 24–35 |
| Gemma E4B | 23–27 | 29–42 |
| Tiny Aya | 10–14 | 25–36 |
| Qwen 3.5 2B | 14–18 | 16–24 |
| Qwen 3.5 4B | 15–19 | 22–32 |

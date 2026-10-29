# Stage 1 findings: structured aliases vs UUIDs

**Model:** Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m  
**Revision:** `91cad51170dc346986eccefdc2dd33a9da36ead9`  
**Design:** 400 deterministic generations; 100 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 100.0% | 100.0% | 68.0% | 96.0% | 96.0% |
| 5 | uuid | 98.0% | 98.0% | 29.0% | 63.0% | 81.0% |
| 20 | structured | 63.0% | 90.0% | 7.0% | 66.0% | 67.0% |
| 20 | uuid | 66.0% | 92.0% | 34.0% | 37.0% | 38.0% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 3.00 | 234.57 | 13.62 | 1.74 | 28.0% |
| 5 | uuid | 33.19 | 385.50 | 49.88 | 4.36 | 34.0% |
| 20 | structured | 3.55 | 639.31 | 14.79 | 5.27 | 59.0% |
| 20 | uuid | 33.46 | 1237.42 | 46.50 | 11.96 | 3.0% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | -2.0 pp | [-5.0, +0.0] pp | 2 / 0 | 0.5 |
| 5 | answer_content_correct | -2.0 pp | [-5.0, +0.0] pp | 2 / 0 | 0.5 |
| 5 | citation_strict_correct | -39.0 pp | [-53.0, -25.0] pp | 52 / 13 | 1.17e-06 |
| 5 | source_binding_exact | -33.0 pp | [-43.0, -23.0] pp | 35 / 2 | 1.02e-08 |
| 20 | answer_exact | +3.0 pp | [-5.0, +11.0] pp | 8 / 11 | 0.648 |
| 20 | answer_content_correct | +2.0 pp | [-5.0, +9.0] pp | 5 / 7 | 0.774 |
| 20 | citation_strict_correct | +27.0 pp | [+17.0, +37.0] pp | 3 / 30 | 1.4e-06 |
| 20 | source_binding_exact | -29.0 pp | [-42.0, -16.0] pp | 41 / 12 | 8.17e-05 |

## Findings

1. **Exact source binding:** Exact binding was 96.0% vs 63.0% at 5 sources, and 66.0% vs 37.0% at 20 sources (structured vs UUID).
2. **Strict citation syntax:** Strict syntax compliance was 68.0% vs 29.0% at 5 sources, and 7.0% vs 34.0% at 20 sources.
3. **Answer content invariance:** Answer content accuracy was 100.0% vs 98.0% at 5 sources, and 90.0% vs 92.0% at 20 sources.
4. **Input token overhead:** UUID prompts imposed a token overhead of +64.3% at 5 sources and +93.6% at 20 sources.
5. **Representation and scale sensitivity:** Performance differences reflect model architecture, capacity, and surface formatting adherence.

## Limitations

- Evaluated on Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m (revision `91cad51170dc346986eccefdc2dd33a9da36ead9`); results reflect this specific checkpoint and quantization.
- Evaluated with deterministic decoding (temperature 0) under fixed seed.
- Single-hop fictional QA only; multi-hop tracking is evaluated separately in MuSiQue.
- Output budget was fixed across conditions; truncation is reported per cell.

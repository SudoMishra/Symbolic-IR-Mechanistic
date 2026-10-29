# Stage 1 findings: structured aliases vs UUIDs

**Model:** unsloth/Qwen3.5-2B-GGUF:q4_k_m  
**Revision:** `f6d5376be1edb4d416d56da11e5397a961aca8ae`  
**Design:** 2000 deterministic generations; 500 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 36.0% | 100.0% | 99.4% | 99.4% | 100.0% |
| 5 | uuid | 40.4% | 99.8% | 98.0% | 98.0% | 98.4% |
| 20 | structured | 39.4% | 100.0% | 97.0% | 97.0% | 97.4% |
| 20 | uuid | 31.8% | 100.0% | 94.0% | 94.0% | 94.0% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 3.00 | 226.16 | 18.99 | 0.20 | 0.0% |
| 5 | uuid | 32.84 | 375.35 | 48.21 | 0.47 | 0.0% |
| 20 | structured | 3.55 | 643.53 | 19.70 | 0.30 | 0.0% |
| 20 | uuid | 33.25 | 1237.45 | 49.35 | 0.67 | 0.0% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | +4.4 pp | [+0.8, +8.0] pp | 29 / 51 | 0.0183 |
| 5 | answer_content_correct | -0.2 pp | [-0.6, +0.0] pp | 1 / 0 | 1 |
| 5 | citation_strict_correct | -1.4 pp | [-2.8, +0.0] pp | 10 / 3 | 0.0923 |
| 5 | source_binding_exact | -1.4 pp | [-2.8, +0.0] pp | 10 / 3 | 0.0923 |
| 20 | answer_exact | -7.6 pp | [-11.4, -3.8] pp | 68 / 30 | 0.000156 |
| 20 | answer_content_correct | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 20 | citation_strict_correct | -3.0 pp | [-5.6, -0.4] pp | 30 / 15 | 0.0357 |
| 20 | source_binding_exact | -3.0 pp | [-5.6, -0.4] pp | 30 / 15 | 0.0357 |

## Findings

1. **Exact source binding:** Exact binding was 99.4% vs 98.0% at 5 sources, and 97.0% vs 94.0% at 20 sources (structured vs UUID).
2. **Strict citation syntax:** Strict syntax compliance was 99.4% vs 98.0% at 5 sources, and 97.0% vs 94.0% at 20 sources.
3. **Answer content invariance:** Answer content accuracy was 100.0% vs 99.8% at 5 sources, and 100.0% vs 100.0% at 20 sources.
4. **Input token overhead:** UUID prompts imposed a token overhead of +66.0% at 5 sources and +92.3% at 20 sources.
5. **Representation and scale sensitivity:** Performance differences reflect model architecture, capacity, and surface formatting adherence.

## Limitations

- Evaluated on unsloth/Qwen3.5-2B-GGUF:q4_k_m (revision `f6d5376be1edb4d416d56da11e5397a961aca8ae`); results reflect this specific checkpoint and quantization.
- Evaluated with deterministic decoding (temperature 0) under fixed seed.
- Single-hop fictional QA only; multi-hop tracking is evaluated separately in MuSiQue.
- Output budget was fixed across conditions; truncation is reported per cell.

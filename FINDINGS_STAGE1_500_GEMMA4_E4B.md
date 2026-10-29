# Stage 1 findings: structured aliases vs UUIDs

**Model:** google/gemma-4-E4B-it-qat-q4_0-gguf  
**Revision:** `c074be2035ce675c963fb1f71df05a0d31ff6be4`  
**Design:** 2000 deterministic generations; 500 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 5 | uuid | 100.0% | 100.0% | 91.8% | 100.0% | 100.0% |
| 20 | structured | 100.0% | 100.0% | 96.2% | 100.0% | 100.0% |
| 20 | uuid | 100.0% | 100.0% | 82.6% | 100.0% | 100.0% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 4.00 | 223.41 | 11.98 | 0.28 | 0.0% |
| 5 | uuid | 34.48 | 375.82 | 42.39 | 0.89 | 8.2% |
| 20 | structured | 4.55 | 651.04 | 12.47 | 0.48 | 3.8% |
| 20 | uuid | 34.76 | 1255.21 | 42.44 | 1.29 | 17.4% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 5 | answer_content_correct | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 5 | citation_strict_correct | -8.2 pp | [-10.6, -5.8] pp | 41 / 0 | 9.09e-13 |
| 5 | source_binding_exact | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 20 | answer_exact | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 20 | answer_content_correct | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 20 | citation_strict_correct | -13.6 pp | [-17.2, -10.0] pp | 81 / 13 | 3.6e-13 |
| 20 | source_binding_exact | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |

## Findings

1. **Exact source binding:** Exact binding was 100.0% vs 100.0% at 5 sources, and 100.0% vs 100.0% at 20 sources (structured vs UUID).
2. **Strict citation syntax:** Strict syntax compliance was 100.0% vs 91.8% at 5 sources, and 96.2% vs 82.6% at 20 sources.
3. **Answer content invariance:** Answer content accuracy was 100.0% vs 100.0% at 5 sources, and 100.0% vs 100.0% at 20 sources.
4. **Input token overhead:** UUID prompts imposed a token overhead of +68.2% at 5 sources and +92.8% at 20 sources.
5. **Representation and scale sensitivity:** Performance differences reflect model architecture, capacity, and surface formatting adherence.

## Limitations

- Evaluated on google/gemma-4-E4B-it-qat-q4_0-gguf (revision `c074be2035ce675c963fb1f71df05a0d31ff6be4`); results reflect this specific checkpoint and quantization.
- Evaluated with deterministic decoding (temperature 0) under fixed seed.
- Single-hop fictional QA only; multi-hop tracking is evaluated separately in MuSiQue.
- Output budget was fixed across conditions; truncation is reported per cell.

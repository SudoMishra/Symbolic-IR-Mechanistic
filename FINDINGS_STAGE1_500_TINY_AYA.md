# Stage 1 findings: structured aliases vs UUIDs

**Model:** CohereLabs/tiny-aya-global-GGUF:q4_k_m  
**Revision:** `a602ea7eeec3a4ad6f77a1b8cf6a53512824922b`  
**Design:** 2000 deterministic generations; 500 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 100.0% | 100.0% | 52.0% | 96.0% | 97.8% |
| 5 | uuid | 100.0% | 100.0% | 64.0% | 79.6% | 79.6% |
| 20 | structured | 99.2% | 99.4% | 43.6% | 76.8% | 80.0% |
| 20 | uuid | 99.6% | 99.8% | 70.0% | 73.6% | 74.4% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 3.00 | 557.83 | 13.08 | 0.23 | 44.0% |
| 5 | uuid | 23.84 | 662.04 | 33.21 | 0.51 | 15.6% |
| 20 | structured | 3.00 | 912.88 | 13.20 | 0.35 | 33.2% |
| 20 | uuid | 24.18 | 1336.42 | 34.41 | 0.81 | 3.6% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 5 | answer_content_correct | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 5 | citation_strict_correct | +12.0 pp | [+6.0, +18.0] pp | 93 / 153 | 0.000158 |
| 5 | source_binding_exact | -16.4 pp | [-20.2, -12.6] pp | 96 / 14 | 3.3e-16 |
| 20 | answer_exact | +0.4 pp | [-0.6, +1.4] pp | 2 / 4 | 0.688 |
| 20 | answer_content_correct | +0.4 pp | [-0.4, +1.2] pp | 1 / 3 | 0.625 |
| 20 | citation_strict_correct | +26.4 pp | [+20.4, +32.2] pp | 63 / 195 | 7.01e-17 |
| 20 | source_binding_exact | -3.2 pp | [-8.4, +2.0] pp | 98 / 82 | 0.263 |

## Findings

1. **Exact source binding:** Exact binding was 96.0% vs 79.6% at 5 sources, and 76.8% vs 73.6% at 20 sources (structured vs UUID).
2. **Strict citation syntax:** Strict syntax compliance was 52.0% vs 64.0% at 5 sources, and 43.6% vs 70.0% at 20 sources.
3. **Answer content invariance:** Answer content accuracy was 100.0% vs 100.0% at 5 sources, and 99.4% vs 99.8% at 20 sources.
4. **Input token overhead:** UUID prompts imposed a token overhead of +18.7% at 5 sources and +46.4% at 20 sources.
5. **Representation and scale sensitivity:** Performance differences reflect model architecture, capacity, and surface formatting adherence.

## Limitations

- Evaluated on CohereLabs/tiny-aya-global-GGUF:q4_k_m (revision `a602ea7eeec3a4ad6f77a1b8cf6a53512824922b`); results reflect this specific checkpoint and quantization.
- Evaluated with deterministic decoding (temperature 0) under fixed seed.
- Single-hop fictional QA only; multi-hop tracking is evaluated separately in MuSiQue.
- Output budget was fixed across conditions; truncation is reported per cell.

# Stage 1 findings: structured aliases vs UUIDs

**Model:** LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m  
**Revision:** `b02009280d04ca03d324d084eeeb965a71141315`  
**Design:** 2000 deterministic generations; 500 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 11.6% | 100.0% | 1.0% | 55.0% | 97.0% |
| 5 | uuid | 8.0% | 99.8% | 10.2% | 13.0% | 75.0% |
| 20 | structured | 10.4% | 96.4% | 0.0% | 3.8% | 75.2% |
| 20 | uuid | 39.8% | 96.2% | 1.8% | 2.2% | 45.8% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 4.00 | 218.30 | 36.99 | 0.18 | 54.0% |
| 5 | uuid | 24.21 | 319.36 | 79.46 | 0.39 | 3.6% |
| 20 | structured | 4.00 | 601.01 | 42.52 | 0.25 | 3.8% |
| 20 | uuid | 24.70 | 1015.01 | 79.86 | 0.47 | 0.6% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | -3.6 pp | [-6.6, -0.8] pp | 37 / 19 | 0.0222 |
| 5 | answer_content_correct | -0.2 pp | [-0.6, +0.0] pp | 1 / 0 | 1 |
| 5 | citation_strict_correct | +9.2 pp | [+6.4, +12.0] pp | 5 / 51 | 1.17e-10 |
| 5 | source_binding_exact | -42.0 pp | [-47.4, -36.6] pp | 243 / 33 | 1.06e-40 |
| 20 | answer_exact | +29.4 pp | [+25.4, +33.6] pp | 4 / 151 | 1.04e-39 |
| 20 | answer_content_correct | -0.2 pp | [-2.4, +2.0] pp | 16 / 15 | 1 |
| 20 | citation_strict_correct | +1.8 pp | [+0.8, +3.0] pp | 0 / 9 | 0.00391 |
| 20 | source_binding_exact | -1.6 pp | [-3.4, +0.0] pp | 13 / 5 | 0.0963 |

## Findings

1. **Exact source binding:** Exact binding was 55.0% vs 13.0% at 5 sources, and 3.8% vs 2.2% at 20 sources (structured vs UUID).
2. **Strict citation syntax:** Strict syntax compliance was 1.0% vs 10.2% at 5 sources, and 0.0% vs 1.8% at 20 sources.
3. **Answer content invariance:** Answer content accuracy was 100.0% vs 99.8% at 5 sources, and 96.4% vs 96.2% at 20 sources.
4. **Input token overhead:** UUID prompts imposed a token overhead of +46.3% at 5 sources and +68.9% at 20 sources.
5. **Representation and scale sensitivity:** Performance differences reflect model architecture, capacity, and surface formatting adherence.

## Limitations

- Evaluated on LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m (revision `b02009280d04ca03d324d084eeeb965a71141315`); results reflect this specific checkpoint and quantization.
- Evaluated with deterministic decoding (temperature 0) under fixed seed.
- Single-hop fictional QA only; multi-hop tracking is evaluated separately in MuSiQue.
- Output budget was fixed across conditions; truncation is reported per cell.

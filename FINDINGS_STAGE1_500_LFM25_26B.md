# Stage 1 findings: structured aliases vs UUIDs

**Model:** LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m  
**Revision:** `e7caca5d835a3901a8e0d63e94009429bafafdfc`  
**Design:** 2000 deterministic generations; 500 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 90.2% | 98.2% | 66.0% | 97.0% | 98.2% |
| 5 | uuid | 83.4% | 99.6% | 95.8% | 96.4% | 97.8% |
| 20 | structured | 60.0% | 66.8% | 40.0% | 62.0% | 68.0% |
| 20 | uuid | 84.8% | 85.4% | 61.8% | 61.8% | 66.4% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 4.00 | 216.30 | 18.91 | 0.23 | 31.0% |
| 5 | uuid | 23.88 | 315.68 | 34.97 | 0.42 | 0.6% |
| 20 | structured | 4.00 | 599.01 | 18.89 | 0.33 | 22.0% |
| 20 | uuid | 24.33 | 1005.52 | 35.75 | 0.59 | 0.0% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | -6.8 pp | [-11.0, -2.6] pp | 74 / 40 | 0.00187 |
| 5 | answer_content_correct | +1.4 pp | [+0.4, +2.6] pp | 1 / 8 | 0.0391 |
| 5 | citation_strict_correct | +29.8 pp | [+25.6, +34.2] pp | 10 / 159 | 1.14e-35 |
| 5 | source_binding_exact | -0.6 pp | [-2.6, +1.4] pp | 15 / 12 | 0.701 |
| 20 | answer_exact | +24.8 pp | [+20.4, +29.4] pp | 20 / 144 | 2.41e-24 |
| 20 | answer_content_correct | +18.6 pp | [+14.4, +22.8] pp | 18 / 111 | 1.54e-17 |
| 20 | citation_strict_correct | +21.8 pp | [+16.2, +27.2] pp | 56 / 165 | 1.17e-13 |
| 20 | source_binding_exact | -0.2 pp | [-5.0, +4.6] pp | 75 / 74 | 1 |

## Findings

1. **Exact source binding:** Exact binding was 97.0% vs 96.4% at 5 sources, and 62.0% vs 61.8% at 20 sources (structured vs UUID).
2. **Strict citation syntax:** Strict syntax compliance was 66.0% vs 95.8% at 5 sources, and 40.0% vs 61.8% at 20 sources.
3. **Answer content invariance:** Answer content accuracy was 98.2% vs 99.6% at 5 sources, and 66.8% vs 85.4% at 20 sources.
4. **Input token overhead:** UUID prompts imposed a token overhead of +45.9% at 5 sources and +67.9% at 20 sources.
5. **Representation and scale sensitivity:** Performance differences reflect model architecture, capacity, and surface formatting adherence.

## Limitations

- Evaluated on LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m (revision `e7caca5d835a3901a8e0d63e94009429bafafdfc`); results reflect this specific checkpoint and quantization.
- Evaluated with deterministic decoding (temperature 0) under fixed seed.
- Single-hop fictional QA only; multi-hop tracking is evaluated separately in MuSiQue.
- Output budget was fixed across conditions; truncation is reported per cell.

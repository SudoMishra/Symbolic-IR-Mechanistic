# Stage 1 findings: structured aliases vs UUIDs

**Model:** Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m  
**Revision:** `d538981f62157dd8d02e8648325a722db3ff9ae8`  
**Design:** 2000 deterministic generations; 500 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 99.4% | 99.4% | 72.8% | 98.6% | 99.0% |
| 5 | uuid | 99.6% | 99.6% | 53.8% | 81.2% | 87.0% |
| 20 | structured | 56.2% | 85.4% | 12.6% | 68.8% | 68.8% |
| 20 | uuid | 65.2% | 88.8% | 36.6% | 40.4% | 41.0% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 3.00 | 234.74 | 13.71 | 0.12 | 25.8% |
| 5 | uuid | 32.84 | 383.93 | 45.77 | 0.37 | 27.4% |
| 20 | structured | 3.55 | 639.10 | 14.89 | 0.20 | 56.2% |
| 20 | uuid | 33.25 | 1233.07 | 46.09 | 0.54 | 3.8% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | +0.2 pp | [-0.4, +0.8] pp | 1 / 2 | 1 |
| 5 | answer_content_correct | +0.2 pp | [-0.4, +1.0] pp | 1 / 2 | 1 |
| 5 | citation_strict_correct | -19.0 pp | [-24.6, -13.2] pp | 165 / 70 | 5.08e-10 |
| 5 | source_binding_exact | -17.4 pp | [-21.0, -14.0] pp | 91 / 4 | 1.68e-22 |
| 20 | answer_exact | +9.0 pp | [+4.8, +13.2] pp | 37 / 82 | 4.53e-05 |
| 20 | answer_content_correct | +3.4 pp | [-0.2, +7.0] pp | 35 / 52 | 0.0857 |
| 20 | citation_strict_correct | +24.0 pp | [+19.2, +28.8] pp | 31 / 151 | 3.81e-20 |
| 20 | source_binding_exact | -28.4 pp | [-34.0, -22.6] pp | 197 / 55 | 6.14e-20 |

## Findings

1. **Exact source binding:** Exact binding was 98.6% vs 81.2% at 5 sources, and 68.8% vs 40.4% at 20 sources (structured vs UUID).
2. **Strict citation syntax:** Strict syntax compliance was 72.8% vs 53.8% at 5 sources, and 12.6% vs 36.6% at 20 sources.
3. **Answer content invariance:** Answer content accuracy was 99.4% vs 99.6% at 5 sources, and 85.4% vs 88.8% at 20 sources.
4. **Input token overhead:** UUID prompts imposed a token overhead of +63.6% at 5 sources and +92.9% at 20 sources.
5. **Representation and scale sensitivity:** Performance differences reflect model architecture, capacity, and surface formatting adherence.

## Limitations

- Evaluated on Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m (revision `d538981f62157dd8d02e8648325a722db3ff9ae8`); results reflect this specific checkpoint and quantization.
- Evaluated with deterministic decoding (temperature 0) under fixed seed.
- Single-hop fictional QA only; multi-hop tracking is evaluated separately in MuSiQue.
- Output budget was fixed across conditions; truncation is reported per cell.

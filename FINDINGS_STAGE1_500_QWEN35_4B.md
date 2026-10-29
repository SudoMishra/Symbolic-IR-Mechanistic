# Stage 1 findings: structured aliases vs UUIDs

**Model:** unsloth/Qwen3.5-4B-GGUF:q4_k_m  
**Revision:** `e87f1764eb865ad3d9be58bc3571d445a6b014ba`  
**Design:** 2000 deterministic generations; 500 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 5 | uuid | 100.0% | 100.0% | 96.0% | 100.0% | 100.0% |
| 20 | structured | 100.0% | 100.0% | 99.8% | 99.8% | 99.8% |
| 20 | uuid | 100.0% | 100.0% | 97.4% | 98.0% | 98.0% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 3.00 | 226.16 | 14.10 | 0.35 | 0.0% |
| 5 | uuid | 32.84 | 375.35 | 43.26 | 0.91 | 4.0% |
| 20 | structured | 3.55 | 643.53 | 14.63 | 0.57 | 0.0% |
| 20 | uuid | 33.25 | 1237.45 | 43.61 | 1.35 | 0.6% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 5 | answer_content_correct | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 5 | citation_strict_correct | -4.0 pp | [-5.8, -2.4] pp | 20 / 0 | 1.91e-06 |
| 5 | source_binding_exact | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 20 | answer_exact | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 20 | answer_content_correct | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 20 | citation_strict_correct | -2.4 pp | [-4.0, -1.0] pp | 13 / 1 | 0.00183 |
| 20 | source_binding_exact | -1.8 pp | [-3.2, -0.6] pp | 10 / 1 | 0.0117 |

## Findings

1. **Exact source binding:** Exact binding was 100.0% vs 100.0% at 5 sources, and 99.8% vs 98.0% at 20 sources (structured vs UUID).
2. **Strict citation syntax:** Strict syntax compliance was 100.0% vs 96.0% at 5 sources, and 99.8% vs 97.4% at 20 sources.
3. **Answer content invariance:** Answer content accuracy was 100.0% vs 100.0% at 5 sources, and 100.0% vs 100.0% at 20 sources.
4. **Input token overhead:** UUID prompts imposed a token overhead of +66.0% at 5 sources and +92.3% at 20 sources.
5. **Representation and scale sensitivity:** Performance differences reflect model architecture, capacity, and surface formatting adherence.

## Limitations

- Evaluated on unsloth/Qwen3.5-4B-GGUF:q4_k_m (revision `e87f1764eb865ad3d9be58bc3571d445a6b014ba`); results reflect this specific checkpoint and quantization.
- Evaluated with deterministic decoding (temperature 0) under fixed seed.
- Single-hop fictional QA only; multi-hop tracking is evaluated separately in MuSiQue.
- Output budget was fixed across conditions; truncation is reported per cell.

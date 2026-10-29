# Stage 1 findings: structured aliases vs UUIDs

**Model:** google/gemma-4-E2B-it-qat-q4_0-gguf  
**Revision:** `e67406c117b34f68ebfe9403d527fa28c5bb74ea`  
**Design:** 2000 deterministic generations; 500 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 83.0% | 100.0% | 98.0% | 99.8% | 100.0% |
| 5 | uuid | 95.2% | 100.0% | 99.4% | 99.6% | 99.8% |
| 20 | structured | 97.6% | 99.8% | 76.4% | 99.2% | 99.6% |
| 20 | uuid | 99.4% | 99.8% | 99.6% | 99.8% | 99.8% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 4.00 | 223.41 | 13.21 | 0.17 | 1.8% |
| 5 | uuid | 34.48 | 375.82 | 43.08 | 0.52 | 0.2% |
| 20 | structured | 4.55 | 651.04 | 12.40 | 0.28 | 22.8% |
| 20 | uuid | 34.76 | 1255.21 | 42.78 | 0.80 | 0.2% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | +12.2 pp | [+9.2, +15.2] pp | 4 / 65 | 3.11e-15 |
| 5 | answer_content_correct | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 5 | citation_strict_correct | +1.4 pp | [+0.0, +2.8] pp | 3 / 10 | 0.0923 |
| 5 | source_binding_exact | -0.2 pp | [-1.0, +0.4] pp | 2 / 1 | 1 |
| 20 | answer_exact | +1.8 pp | [+0.4, +3.4] pp | 3 / 12 | 0.0352 |
| 20 | answer_content_correct | +0.0 pp | [-0.6, +0.6] pp | 1 / 1 | 1 |
| 20 | citation_strict_correct | +23.2 pp | [+19.4, +27.0] pp | 2 / 118 | 1.09e-32 |
| 20 | source_binding_exact | +0.6 pp | [-0.2, +1.6] pp | 1 / 4 | 0.375 |

## Findings

1. **Exact source binding:** Exact binding was 99.8% vs 99.6% at 5 sources, and 99.2% vs 99.8% at 20 sources (structured vs UUID).
2. **Strict citation syntax:** Strict syntax compliance was 98.0% vs 99.4% at 5 sources, and 76.4% vs 99.6% at 20 sources.
3. **Answer content invariance:** Answer content accuracy was 100.0% vs 100.0% at 5 sources, and 99.8% vs 99.8% at 20 sources.
4. **Input token overhead:** UUID prompts imposed a token overhead of +68.2% at 5 sources and +92.8% at 20 sources.
5. **Representation and scale sensitivity:** Performance differences reflect model architecture, capacity, and surface formatting adherence.

## Limitations

- Evaluated on google/gemma-4-E2B-it-qat-q4_0-gguf (revision `e67406c117b34f68ebfe9403d527fa28c5bb74ea`); results reflect this specific checkpoint and quantization.
- Evaluated with deterministic decoding (temperature 0) under fixed seed.
- Single-hop fictional QA only; multi-hop tracking is evaluated separately in MuSiQue.
- Output budget was fixed across conditions; truncation is reported per cell.

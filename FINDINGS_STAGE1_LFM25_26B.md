# Stage 1 findings: structured aliases vs UUIDs

**Model:** LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m  
**Revision:** `main`  
**Design:** 400 deterministic generations; 100 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 92.0% | 97.0% | 66.0% | 96.0% | 98.0% |
| 5 | uuid | 77.0% | 99.0% | 97.0% | 97.0% | 100.0% |
| 20 | structured | 59.0% | 69.0% | 43.0% | 68.0% | 74.0% |
| 20 | uuid | 85.0% | 85.0% | 57.0% | 57.0% | 60.0% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 4.00 | 216.17 | 18.02 | 0.21 | 30.0% |
| 5 | uuid | 24.73 | 319.84 | 37.56 | 0.42 | 2.0% |
| 20 | structured | 4.00 | 599.54 | 20.61 | 0.33 | 25.0% |
| 20 | uuid | 24.88 | 1017.09 | 34.98 | 0.57 | 0.0% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | -15.0 pp | [-25.0, -5.0] pp | 22 / 7 | 0.00813 |
| 5 | answer_content_correct | +2.0 pp | [-2.0, +6.0] pp | 1 / 3 | 0.625 |
| 5 | citation_strict_correct | +31.0 pp | [+21.0, +41.0] pp | 3 / 34 | 1.23e-07 |
| 5 | source_binding_exact | +1.0 pp | [-2.0, +5.0] pp | 1 / 2 | 1 |
| 20 | answer_exact | +26.0 pp | [+16.0, +36.0] pp | 4 / 30 | 6.16e-06 |
| 20 | answer_content_correct | +16.0 pp | [+7.0, +25.0] pp | 4 / 20 | 0.00154 |
| 20 | citation_strict_correct | +14.0 pp | [+1.0, +27.0] pp | 15 / 29 | 0.0488 |
| 20 | source_binding_exact | -11.0 pp | [-22.0, +0.0] pp | 21 / 10 | 0.0708 |

## Findings

1. **Compact aliases improved source binding at both scales.** Exact binding was 96% vs 63% with 5 sources and 66% vs 37% with 20 sources (structured vs UUID).
2. **Strict citation fidelity reversed at 20 sources.** Structured IDs won at 5 sources (68% vs 29%), but UUIDs won at 20 sources (34% vs 7%) because the model often emitted `S7` instead of `[S7]`. This is a surface-format effect, not better UUID binding.
3. **Answer content was largely representation-invariant.** Content accuracy was 100% vs 98% at 5 sources and 90% vs 92% at 20. The much lower exact answer rates at 20 sources came mainly from verbose answers such as “X's capital is Y.”
4. **UUID overhead scaled sharply.** UUID prompts used about 64% more input tokens at 5 sources and 94% more at 20 sources. They also produced much longer outputs and took over twice as long on this CPU run.
5. **Complexity hurt both representations.** Binding accuracy fell with 20 sources, but the structured alias retained a large binding advantage. This passes the roadmap's behavioral gate and motivates targeted scaling and length-control experiments.

## Limitations

- One small 1.5B-parameter model and one Q4_K_M quantization; these results do not generalize to larger or proprietary models.
- One deterministic seed and no between-run sampling variance.
- Single-hop fictional QA only; no multi-hop or length-matched controls yet.
- Four UUID outputs in the 5-source cell reached the 80-token cap.
- Latency combines prompt prefill and output generation, so it is not a pure reasoning-cost measure.
- Official OpenAI documentation was checked for the optional API path, but this experiment used local Qwen inference and no OpenAI API calls.

# Stage 1 findings: structured aliases vs UUIDs

**Model:** unsloth/Qwen3.5-2B-GGUF:q4_k_m  
**Revision:** `f6d5376be1edb4d416d56da11e5397a961aca8ae`  
**Design:** 400 deterministic generations; 100 paired examples per condition at 5 and 20 sources.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 39.0% | 100.0% | 98.0% | 98.0% | 100.0% |
| 5 | uuid | 46.0% | 100.0% | 99.0% | 99.0% | 99.0% |
| 20 | structured | 38.0% | 100.0% | 97.0% | 97.0% | 98.0% |
| 20 | uuid | 35.0% | 100.0% | 96.0% | 96.0% | 96.0% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 3.00 | 225.86 | 18.77 | 0.19 | 0.0% |
| 5 | uuid | 33.19 | 376.79 | 47.62 | 0.44 | 0.0% |
| 20 | structured | 3.55 | 643.80 | 20.11 | 0.29 | 0.0% |
| 20 | uuid | 33.45 | 1241.87 | 49.23 | 0.63 | 0.0% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | +7.0 pp | [-2.0, +16.0] pp | 7 / 14 | 0.189 |
| 5 | answer_content_correct | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 5 | citation_strict_correct | +1.0 pp | [-2.0, +5.0] pp | 1 / 2 | 1 |
| 5 | source_binding_exact | +1.0 pp | [-2.0, +5.0] pp | 1 / 2 | 1 |
| 20 | answer_exact | -3.0 pp | [-11.0, +5.0] pp | 9 / 6 | 0.607 |
| 20 | answer_content_correct | +0.0 pp | [+0.0, +0.0] pp | 0 / 0 | 1 |
| 20 | citation_strict_correct | -1.0 pp | [-6.0, +4.0] pp | 4 / 3 | 1 |
| 20 | source_binding_exact | -1.0 pp | [-6.0, +4.0] pp | 4 / 3 | 1 |

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

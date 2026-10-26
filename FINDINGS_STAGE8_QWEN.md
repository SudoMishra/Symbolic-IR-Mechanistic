# Stage 8: synthetic PII and entity canonicalization

**Design:** 40 synthetic account-resolution examples × four entity representations = 160 deterministic generations through `Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 85.0% | 5.0% | 5.0% | 5.0% | 95.0% | 2579.5 | 16.6 | 0.63s |
| 15 | random_masked | 90.0% | 10.0% | 0.0% | 0.0% | 0.0% | 2433.8 | 9.2 | 0.53s |
| 15 | untyped | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | 2359.1 | 6.8 | 0.49s |
| 15 | typed | 95.0% | 5.0% | 0.0% | 0.0% | 0.0% | 2359.1 | 6.8 | 0.49s |
| 20 | raw | 95.0% | 5.0% | 0.0% | 0.0% | 100.0% | 3410.8 | 17.0 | 0.85s |
| 20 | random_masked | 80.0% | 20.0% | 0.0% | 0.0% | 0.0% | 3218.1 | 10.7 | 0.75s |
| 20 | untyped | 85.0% | 15.0% | 0.0% | 0.0% | 0.0% | 3121.8 | 6.4 | 0.69s |
| 20 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3121.8 | 6.2 | 0.69s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +17.5 pp [+7.5, +30.0] | 0/7 | 0.0156 | +0.0 |
| typed − random_masked | +12.5 pp [+0.0, +25.0] | 1/6 | 0.125 | -85.5 |
| typed − raw | +7.5 pp [+0.0, +17.5] | 0/3 | 0.25 | -254.7 |

## Checkpoint 8

**Decision: generalization signal present.** Typed minus untyped accuracy is +17.5 pp (95% CI [+7.5, +30.0]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

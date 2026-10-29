# Stage 8: synthetic PII and entity canonicalization

**Design:** 500 synthetic account-resolution examples × four entity representations = 2000 deterministic generations through `Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 95.6% | 2.0% | 0.0% | 2.4% | 98.8% | 2580.2 | 16.9 | 0.66s |
| 15 | random_masked | 90.0% | 8.8% | 1.2% | 0.0% | 0.0% | 2435.0 | 9.1 | 0.56s |
| 15 | untyped | 83.2% | 16.8% | 0.0% | 0.0% | 0.0% | 2359.7 | 6.8 | 0.53s |
| 15 | typed | 93.2% | 6.8% | 0.0% | 0.0% | 0.0% | 2359.7 | 6.5 | 0.52s |
| 20 | raw | 94.0% | 2.4% | 0.0% | 3.6% | 98.0% | 3412.1 | 17.0 | 0.90s |
| 20 | random_masked | 74.0% | 23.6% | 2.0% | 0.4% | 0.0% | 3219.5 | 9.8 | 0.78s |
| 20 | untyped | 78.8% | 21.2% | 0.0% | 0.0% | 0.0% | 3122.8 | 6.8 | 0.73s |
| 20 | typed | 91.6% | 8.0% | 0.4% | 0.0% | 0.0% | 3122.8 | 6.0 | 0.73s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +11.4 pp [+8.0, +14.6] | 9/66 | 7.66e-12 | +0.0 |
| typed − random_masked | +10.4 pp [+6.4, +14.4] | 29/81 | 7.29e-07 | -86.0 |
| typed − raw | -2.4 pp [-5.2, +0.4] | 34/22 | 0.141 | -254.9 |

## Checkpoint 8

**Decision: generalization signal present.** Typed minus untyped accuracy is +11.4 pp (95% CI [+8.0, +14.6]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

# Stage 8: synthetic PII and entity canonicalization

**Design:** 40 synthetic account-resolution examples × four entity representations = 160 deterministic generations through `LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 40.0% | 0.0% | 0.0% | 60.0% | 75.0% | 2378.4 | 7.3 | 0.33s |
| 15 | random_masked | 5.0% | 95.0% | 0.0% | 0.0% | 0.0% | 2351.2 | 8.1 | 0.32s |
| 15 | untyped | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 2364.7 | 9.0 | 0.33s |
| 15 | typed | 10.0% | 85.0% | 5.0% | 0.0% | 0.0% | 2394.7 | 10.2 | 0.34s |
| 20 | raw | 15.0% | 25.0% | 0.0% | 60.0% | 95.0% | 3146.6 | 9.3 | 0.46s |
| 20 | random_masked | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 3113.2 | 7.0 | 0.44s |
| 20 | untyped | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 3128.6 | 14.7 | 0.48s |
| 20 | typed | 5.0% | 80.0% | 15.0% | 0.0% | 0.0% | 3168.6 | 16.6 | 0.49s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +7.5 pp [+0.0, +17.5] | 0/3 | 0.25 | +35.0 |
| typed − random_masked | +5.0 pp [+0.0, +12.5] | 0/2 | 0.5 | +49.5 |
| typed − raw | -20.0 pp [-35.0, -5.0] | 9/1 | 0.0215 | +19.2 |

## Checkpoint 8

**Decision: no confirmed improvement yet.** Typed minus untyped accuracy is +7.5 pp (95% CI [+0.0, +17.5]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

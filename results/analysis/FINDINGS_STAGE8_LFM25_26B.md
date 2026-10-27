# Stage 8: synthetic PII and entity canonicalization

**Design:** 40 synthetic account-resolution examples × four entity representations = 160 deterministic generations through `LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 95.0% | 0.0% | 0.0% | 5.0% | 95.0% | 2345.9 | 7.9 | 0.67s |
| 15 | random_masked | 45.0% | 40.0% | 0.0% | 15.0% | 0.0% | 2318.1 | 9.0 | 0.67s |
| 15 | untyped | 40.0% | 60.0% | 0.0% | 0.0% | 0.0% | 2332.2 | 9.8 | 0.68s |
| 15 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2362.2 | 5.0 | 0.64s |
| 20 | raw | 90.0% | 10.0% | 0.0% | 0.0% | 100.0% | 3102.8 | 8.0 | 0.91s |
| 20 | random_masked | 60.0% | 35.0% | 5.0% | 0.0% | 0.0% | 3068.6 | 7.5 | 0.89s |
| 20 | untyped | 15.0% | 85.0% | 0.0% | 0.0% | 0.0% | 3084.8 | 12.3 | 0.94s |
| 20 | typed | 95.0% | 5.0% | 0.0% | 0.0% | 0.0% | 3124.8 | 5.0 | 0.88s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +70.0 pp [+52.5, +85.0] | 1/29 | 5.77e-08 | +35.0 |
| typed − random_masked | +45.0 pp [+30.0, +60.0] | 0/18 | 7.63e-06 | +50.2 |
| typed − raw | +5.0 pp [-5.0, +15.0] | 1/3 | 0.625 | +19.2 |

## Checkpoint 8

**Decision: generalization signal present.** Typed minus untyped accuracy is +70.0 pp (95% CI [+52.5, +85.0]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

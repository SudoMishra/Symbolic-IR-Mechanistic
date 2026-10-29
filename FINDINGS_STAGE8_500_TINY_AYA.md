# Stage 8: synthetic PII and entity canonicalization

**Design:** 500 synthetic account-resolution examples × four entity representations = 2000 deterministic generations through `CohereLabs/tiny-aya-global-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 87.6% | 8.0% | 0.0% | 4.4% | 100.0% | 2683.1 | 16.3 | 1.18s |
| 15 | random_masked | 79.2% | 14.0% | 0.0% | 6.8% | 0.0% | 2657.5 | 13.2 | 1.12s |
| 15 | untyped | 94.0% | 6.0% | 0.0% | 0.0% | 0.0% | 2623.9 | 9.5 | 1.05s |
| 15 | typed | 99.2% | 0.8% | 0.0% | 0.0% | 0.0% | 2654.9 | 7.7 | 1.04s |
| 20 | raw | 77.2% | 18.4% | 0.0% | 4.4% | 100.0% | 3435.0 | 19.1 | 1.62s |
| 20 | random_masked | 76.4% | 17.2% | 0.4% | 6.0% | 0.0% | 3402.3 | 11.3 | 1.48s |
| 20 | untyped | 88.4% | 11.6% | 0.0% | 0.0% | 0.0% | 3357.0 | 9.3 | 1.43s |
| 20 | typed | 96.0% | 4.0% | 0.0% | 0.0% | 0.0% | 3398.0 | 8.3 | 1.44s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +6.4 pp [+4.0, +9.0] | 5/37 | 4.43e-07 | +36.0 |
| typed − random_masked | +19.8 pp [+16.0, +23.8] | 10/109 | 3.52e-22 | -3.5 |
| typed − raw | +15.2 pp [+11.8, +18.8] | 9/85 | 1.2e-16 | -32.6 |

## Checkpoint 8

**Decision: generalization signal present.** Typed minus untyped accuracy is +6.4 pp (95% CI [+4.0, +9.0]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

# Stage 8: synthetic PII and entity canonicalization

**Design:** 500 synthetic account-resolution examples × four entity representations = 2000 deterministic generations through `LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 28.4% | 2.4% | 0.0% | 69.2% | 92.0% | 2380.3 | 7.7 | 0.35s |
| 15 | random_masked | 4.0% | 94.8% | 0.0% | 1.2% | 0.0% | 2355.8 | 8.7 | 0.35s |
| 15 | untyped | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 2366.6 | 9.1 | 0.35s |
| 15 | typed | 27.2% | 67.6% | 5.2% | 0.0% | 0.0% | 2396.6 | 11.6 | 0.37s |
| 20 | raw | 30.4% | 16.4% | 0.0% | 53.2% | 92.0% | 3148.4 | 9.5 | 0.48s |
| 20 | random_masked | 6.4% | 92.0% | 0.8% | 0.8% | 0.0% | 3116.7 | 7.6 | 0.47s |
| 20 | untyped | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 3130.3 | 12.3 | 0.49s |
| 20 | typed | 16.8% | 75.2% | 8.0% | 0.0% | 0.0% | 3170.3 | 14.9 | 0.51s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +22.0 pp [+18.4, +25.6] | 0/110 | 1.54e-33 | +35.0 |
| typed − random_masked | +16.8 pp [+13.0, +20.6] | 11/95 | 7.73e-18 | +47.2 |
| typed − raw | -7.4 pp [-12.0, -2.8] | 90/53 | 0.00249 | +19.1 |

## Checkpoint 8

**Decision: generalization signal present.** Typed minus untyped accuracy is +22.0 pp (95% CI [+18.4, +25.6]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

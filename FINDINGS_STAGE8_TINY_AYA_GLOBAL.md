# Stage 8: synthetic PII and entity canonicalization

**Design:** 40 synthetic account-resolution examples × four entity representations = 160 deterministic generations through `CohereLabs/tiny-aya-global-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 85.0% | 10.0% | 0.0% | 5.0% | 100.0% | 2682.9 | 15.9 | 1.16s |
| 15 | random_masked | 85.0% | 5.0% | 0.0% | 10.0% | 0.0% | 2654.4 | 14.9 | 1.12s |
| 15 | untyped | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2623.2 | 9.0 | 1.02s |
| 15 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2654.2 | 8.5 | 1.03s |
| 20 | raw | 90.0% | 10.0% | 0.0% | 0.0% | 100.0% | 3434.4 | 18.6 | 1.59s |
| 20 | random_masked | 80.0% | 10.0% | 0.0% | 10.0% | 0.0% | 3399.8 | 9.6 | 1.44s |
| 20 | untyped | 95.0% | 5.0% | 0.0% | 0.0% | 0.0% | 3355.8 | 9.0 | 1.41s |
| 20 | typed | 95.0% | 0.0% | 5.0% | 0.0% | 0.0% | 3396.8 | 9.4 | 1.44s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +0.0 pp [+0.0, +0.0] | 0/0 | 1 | +36.0 |
| typed − random_masked | +15.0 pp [+5.0, +27.5] | 0/6 | 0.0312 | -1.6 |
| typed − raw | +10.0 pp [+0.0, +22.5] | 1/5 | 0.219 | -33.1 |

## Checkpoint 8

**Decision: no confirmed improvement yet.** Typed minus untyped accuracy is +0.0 pp (95% CI [+0.0, +0.0]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

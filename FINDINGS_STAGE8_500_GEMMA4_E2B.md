# Stage 8: synthetic PII and entity canonicalization

**Design:** 500 synthetic account-resolution examples × four entity representations = 2000 deterministic generations through `google/gemma-4-E2B-it-qat-q4_0-gguf`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 2599.8 | 16.0 | 0.94s |
| 15 | random_masked | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2432.6 | 8.0 | 0.77s |
| 15 | untyped | 83.6% | 16.4% | 0.0% | 0.0% | 0.0% | 2358.1 | 7.5 | 0.74s |
| 15 | typed | 98.8% | 0.8% | 0.4% | 0.0% | 0.0% | 2358.1 | 5.8 | 0.72s |
| 20 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 3444.3 | 16.0 | 1.26s |
| 20 | random_masked | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3222.7 | 8.1 | 1.06s |
| 20 | untyped | 88.0% | 12.0% | 0.0% | 0.0% | 0.0% | 3127.1 | 7.3 | 1.02s |
| 20 | typed | 98.8% | 1.2% | 0.0% | 0.0% | 0.0% | 3127.1 | 5.9 | 1.00s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +13.0 pp [+10.0, +16.2] | 2/67 | 8.19e-18 | +0.0 |
| typed − random_masked | -1.2 pp [-2.2, -0.4] | 6/0 | 0.0312 | -85.0 |
| typed − raw | -1.2 pp [-2.2, -0.4] | 6/0 | 0.0312 | -279.4 |

## Checkpoint 8

**Decision: generalization signal present.** Typed minus untyped accuracy is +13.0 pp (95% CI [+10.0, +16.2]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

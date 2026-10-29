# Stage 8: synthetic PII and entity canonicalization

**Design:** 500 synthetic account-resolution examples × four entity representations = 2000 deterministic generations through `google/gemma-4-E4B-it-qat-q4_0-gguf`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 2599.8 | 16.0 | 1.49s |
| 15 | random_masked | 99.6% | 0.4% | 0.0% | 0.0% | 0.0% | 2432.6 | 8.0 | 1.25s |
| 15 | untyped | 85.6% | 12.0% | 0.0% | 2.4% | 0.0% | 2358.1 | 7.9 | 1.21s |
| 15 | typed | 99.6% | 0.4% | 0.0% | 0.0% | 0.0% | 2358.1 | 5.8 | 1.18s |
| 20 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 3444.3 | 16.0 | 1.97s |
| 20 | random_masked | 99.6% | 0.4% | 0.0% | 0.0% | 0.0% | 3222.7 | 8.1 | 1.69s |
| 20 | untyped | 87.2% | 5.6% | 0.0% | 7.2% | 0.0% | 3127.1 | 7.8 | 1.63s |
| 20 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3127.1 | 5.9 | 1.60s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +13.4 pp [+10.4, +16.4] | 0/67 | 1.36e-20 | +0.0 |
| typed − random_masked | +0.2 pp [-0.4, +1.0] | 1/2 | 1 | -85.0 |
| typed − raw | -0.2 pp [-0.6, +0.0] | 1/0 | 1 | -279.4 |

## Checkpoint 8

**Decision: generalization signal present.** Typed minus untyped accuracy is +13.4 pp (95% CI [+10.4, +16.4]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

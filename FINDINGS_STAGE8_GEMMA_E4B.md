# Stage 8: synthetic PII and entity canonicalization

**Design:** 40 synthetic account-resolution examples × four entity representations = 160 deterministic generations through `google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 2598.6 | 16.0 | 1.44s |
| 15 | random_masked | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2431.4 | 8.3 | 1.20s |
| 15 | untyped | 90.0% | 10.0% | 0.0% | 0.0% | 0.0% | 2357.4 | 8.0 | 1.16s |
| 15 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2357.4 | 5.8 | 1.12s |
| 20 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 3443.7 | 16.0 | 1.91s |
| 20 | random_masked | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3221.4 | 7.9 | 1.63s |
| 20 | untyped | 95.0% | 5.0% | 0.0% | 0.0% | 0.0% | 3126.2 | 8.1 | 1.59s |
| 20 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3126.2 | 6.0 | 1.54s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +7.5 pp [+0.0, +17.5] | 0/3 | 0.25 | +0.0 |
| typed − random_masked | +0.0 pp [+0.0, +0.0] | 0/0 | 1 | -84.7 |
| typed − raw | +0.0 pp [+0.0, +0.0] | 0/0 | 1 | -279.4 |

## Checkpoint 8

**Decision: no confirmed improvement yet.** Typed minus untyped accuracy is +7.5 pp (95% CI [+0.0, +17.5]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

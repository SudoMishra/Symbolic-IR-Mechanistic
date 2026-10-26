# Stage 8: synthetic PII and entity canonicalization

**Design:** 40 synthetic account-resolution examples × four entity representations = 160 deterministic generations through `google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 2598.6 | 16.0 | 0.89s |
| 15 | random_masked | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2431.4 | 8.2 | 0.73s |
| 15 | untyped | 90.0% | 10.0% | 0.0% | 0.0% | 0.0% | 2357.4 | 7.3 | 0.69s |
| 15 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2357.4 | 5.8 | 0.67s |
| 20 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 3443.7 | 16.0 | 1.20s |
| 20 | random_masked | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3221.4 | 8.0 | 1.01s |
| 20 | untyped | 95.0% | 5.0% | 0.0% | 0.0% | 0.0% | 3126.2 | 7.3 | 0.97s |
| 20 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3126.2 | 6.0 | 0.95s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +7.5 pp [+0.0, +17.5] | 0/3 | 0.25 | +0.0 |
| typed − random_masked | +0.0 pp [+0.0, +0.0] | 0/0 | 1 | -84.7 |
| typed − raw | +0.0 pp [+0.0, +0.0] | 0/0 | 1 | -279.4 |

## Checkpoint 8

**Decision: no confirmed improvement yet.** Typed minus untyped accuracy is +7.5 pp (95% CI [+0.0, +17.5]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

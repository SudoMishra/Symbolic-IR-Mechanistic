# Stage 8: synthetic PII and entity canonicalization

**Design:** 500 synthetic account-resolution examples × four entity representations = 2000 deterministic generations through `unsloth/Qwen3.5-4B-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 2567.1 | 17.0 | 1.59s |
| 15 | random_masked | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2423.2 | 10.1 | 1.39s |
| 15 | untyped | 99.6% | 0.4% | 0.0% | 0.0% | 0.0% | 2348.1 | 8.3 | 1.33s |
| 15 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2348.1 | 7.3 | 1.31s |
| 20 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 3399.2 | 17.0 | 2.04s |
| 20 | random_masked | 99.6% | 0.4% | 0.0% | 0.0% | 0.0% | 3208.6 | 10.3 | 1.82s |
| 20 | untyped | 99.6% | 0.4% | 0.0% | 0.0% | 0.0% | 3112.1 | 8.3 | 1.74s |
| 20 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3112.1 | 7.4 | 1.73s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +0.4 pp [+0.0, +1.0] | 0/2 | 0.5 | +0.0 |
| typed − random_masked | +0.2 pp [+0.0, +0.6] | 0/1 | 1 | -85.8 |
| typed − raw | +0.0 pp [+0.0, +0.0] | 0/0 | 1 | -253.1 |

## Checkpoint 8

**Decision: no confirmed improvement yet.** Typed minus untyped accuracy is +0.4 pp (95% CI [+0.0, +1.0]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

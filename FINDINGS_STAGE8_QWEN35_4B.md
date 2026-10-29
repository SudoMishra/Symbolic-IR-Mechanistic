# Stage 8: synthetic PII and entity canonicalization

**Design:** 40 synthetic account-resolution examples × four entity representations = 160 deterministic generations through `unsloth/Qwen3.5-4B-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 2566.3 | 17.0 | 1.56s |
| 15 | random_masked | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2421.9 | 10.3 | 1.37s |
| 15 | untyped | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2347.4 | 8.4 | 1.30s |
| 15 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2347.4 | 7.5 | 1.29s |
| 20 | raw | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 3398.2 | 17.0 | 2.01s |
| 20 | random_masked | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3207.3 | 10.2 | 1.79s |
| 20 | untyped | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3111.2 | 8.3 | 1.71s |
| 20 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3111.2 | 7.7 | 1.70s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +0.0 pp [+0.0, +0.0] | 0/0 | 1 | +0.0 |
| typed − random_masked | +0.0 pp [+0.0, +0.0] | 0/0 | 1 | -85.4 |
| typed − raw | +0.0 pp [+0.0, +0.0] | 0/0 | 1 | -253.0 |

## Checkpoint 8

**Decision: no confirmed improvement yet.** Typed minus untyped accuracy is +0.0 pp (95% CI [+0.0, +0.0]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

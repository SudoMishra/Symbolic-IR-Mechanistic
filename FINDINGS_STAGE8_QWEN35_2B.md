# Stage 8: synthetic PII and entity canonicalization

**Design:** 40 synthetic account-resolution examples × four entity representations = 160 deterministic generations through `unsloth/Qwen3.5-2B-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 40.0% | 60.0% | 0.0% | 0.0% | 100.0% | 2566.3 | 34.9 | 0.81s |
| 15 | random_masked | 60.0% | 40.0% | 0.0% | 0.0% | 0.0% | 2421.9 | 20.8 | 0.66s |
| 15 | untyped | 95.0% | 5.0% | 0.0% | 0.0% | 0.0% | 2347.4 | 8.8 | 0.55s |
| 15 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2347.4 | 7.0 | 0.53s |
| 20 | raw | 50.0% | 50.0% | 0.0% | 0.0% | 100.0% | 3398.2 | 32.1 | 0.97s |
| 20 | random_masked | 75.0% | 25.0% | 0.0% | 0.0% | 0.0% | 3207.3 | 14.7 | 0.78s |
| 20 | untyped | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3111.2 | 9.0 | 0.72s |
| 20 | typed | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3111.2 | 7.4 | 0.70s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +2.5 pp [+0.0, +7.5] | 0/1 | 1 | +0.0 |
| typed − random_masked | +32.5 pp [+17.5, +47.5] | 0/13 | 0.000244 | -85.4 |
| typed − raw | +55.0 pp [+40.0, +70.0] | 0/22 | 4.77e-07 | -253.0 |

## Checkpoint 8

**Decision: no confirmed improvement yet.** Typed minus untyped accuracy is +2.5 pp (95% CI [+0.0, +7.5]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

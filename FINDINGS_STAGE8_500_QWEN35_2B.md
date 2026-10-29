# Stage 8: synthetic PII and entity canonicalization

**Design:** 500 synthetic account-resolution examples × four entity representations = 2000 deterministic generations through `unsloth/Qwen3.5-2B-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 48.8% | 50.8% | 0.0% | 0.4% | 100.0% | 2567.1 | 32.4 | 0.81s |
| 15 | random_masked | 58.0% | 40.8% | 0.0% | 1.2% | 0.0% | 2423.2 | 19.0 | 0.66s |
| 15 | untyped | 98.0% | 1.6% | 0.0% | 0.4% | 0.0% | 2348.1 | 8.9 | 0.56s |
| 15 | typed | 99.2% | 0.8% | 0.0% | 0.0% | 0.0% | 2348.1 | 7.0 | 0.55s |
| 20 | raw | 48.4% | 51.6% | 0.0% | 0.0% | 100.0% | 3399.2 | 32.7 | 1.00s |
| 20 | random_masked | 64.0% | 36.0% | 0.0% | 0.0% | 0.0% | 3208.6 | 18.7 | 0.84s |
| 20 | untyped | 95.2% | 4.8% | 0.0% | 0.0% | 0.0% | 3112.1 | 9.0 | 0.74s |
| 20 | typed | 98.0% | 2.0% | 0.0% | 0.0% | 0.0% | 3112.1 | 7.1 | 0.72s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +2.0 pp [+0.6, +3.4] | 2/12 | 0.0129 | +0.0 |
| typed − random_masked | +37.6 pp [+33.4, +42.0] | 4/192 | 1.21e-51 | -85.8 |
| typed − raw | +50.0 pp [+45.6, +54.6] | 3/253 | 4.83e-71 | -253.1 |

## Checkpoint 8

**Decision: generalization signal present.** Typed minus untyped accuracy is +2.0 pp (95% CI [+0.6, +3.4]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

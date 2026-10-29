# Stage 8: synthetic PII and entity canonicalization

**Design:** 500 synthetic account-resolution examples × four entity representations = 2000 deterministic generations through `LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m`. Every paired prompt uses the same `[S1]` source labels, task facts, source order, question, and answer mapping; only entity surface form changes. Citations are not requested.

| Sources | Representation | Accuracy | Wrong existing entity | Hallucinated entity | Invalid output | Any raw-PII leakage | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | raw | 96.0% | 4.0% | 0.0% | 0.0% | 100.0% | 2346.7 | 8.1 | 0.71s |
| 15 | random_masked | 58.4% | 30.4% | 0.0% | 11.2% | 0.0% | 2321.2 | 9.0 | 0.71s |
| 15 | untyped | 19.2% | 80.8% | 0.0% | 0.0% | 0.0% | 2332.9 | 10.1 | 0.73s |
| 15 | typed | 99.2% | 0.8% | 0.0% | 0.0% | 0.0% | 2362.9 | 5.0 | 0.69s |
| 20 | raw | 93.2% | 5.6% | 0.4% | 0.8% | 98.8% | 3104.1 | 8.0 | 0.95s |
| 20 | random_masked | 54.8% | 32.4% | 0.0% | 12.8% | 0.0% | 3071.0 | 7.3 | 0.93s |
| 20 | untyped | 17.2% | 82.8% | 0.0% | 0.0% | 0.0% | 3086.0 | 12.2 | 0.98s |
| 20 | typed | 94.8% | 5.2% | 0.0% | 0.0% | 0.0% | 3126.0 | 5.0 | 0.92s |

## Paired effects

Accuracy effects are right condition minus left condition; intervals use 5,000 paired bootstrap resamples.

| Contrast | Accuracy delta (95% CI) | Better only left/right | Exact p | Input-token delta |
|---|---:|---:|---:|---:|
| typed − untyped | +78.8 pp [+75.0, +82.4] | 2/396 | 2.46e-115 | +35.0 |
| typed − random_masked | +40.4 pp [+35.8, +44.8] | 9/211 | 3.49e-51 | +48.4 |
| typed − raw | +2.4 pp [-0.2, +5.0] | 15/27 | 0.0884 | +19.1 |

## Checkpoint 8

**Decision: generalization signal present.** Typed minus untyped accuracy is +78.8 pp (95% CI [+75.0, +82.4]) while holding source labels fixed. All data are synthetic; masking reduces exposure of raw values but is not a complete privacy or security system.

# Stage 6: explicit vs implicit symbolic compression

**Design:** 80 semantic examples × 3 identifier formats = 240 paired forward passes through `LiquidAI/LFM2.5-1.2B-Instruct`. The model has 16 transformer blocks plus the embedding state (17 stored layers) and hidden width 2048.

The same source order, source facts, question, answer, and relevant-source set are used across `[S1]`, compact arbitrary, and UUID conditions. Answer and citation states are teacher-forced so token spans align; they are representation measurements, not generated-answer accuracy estimates.

All intervals are 5,000-replicate paired bootstraps over complete semantic examples.

## Structured versus UUID representation similarity

| Layer | Source-label cosine | Source-fact cosine | Question cosine | Pre-answer cosine | Answer cosine | Pre-citation cosine | Citation cosine |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.643 [0.642, 0.644] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.615 [0.611, 0.619] |
| 4 | 0.451 [0.449, 0.452] | 0.978 [0.978, 0.979] | 0.999 [0.999, 0.999] | 1.000 [1.000, 1.000] | 0.998 [0.997, 0.998] | 0.998 [0.997, 0.998] | 0.551 [0.548, 0.555] |
| 8 | 0.585 [0.583, 0.587] | 0.975 [0.975, 0.976] | 0.998 [0.998, 0.998] | 0.995 [0.995, 0.996] | 0.981 [0.978, 0.984] | 0.990 [0.989, 0.991] | 0.580 [0.578, 0.583] |
| 12 | 0.498 [0.496, 0.500] | 0.959 [0.959, 0.960] | 0.994 [0.993, 0.994] | 0.986 [0.985, 0.987] | 0.972 [0.969, 0.975] | 0.966 [0.965, 0.967] | 0.604 [0.601, 0.607] |
| 16 | 0.218 [0.216, 0.220] | 0.978 [0.978, 0.979] | 0.983 [0.982, 0.985] | 0.958 [0.954, 0.961] | 0.964 [0.961, 0.968] | 0.598 [0.584, 0.611] | 0.372 [0.366, 0.377] |

## Source-identity geometry

Alignment margin is matched-source cosine minus the mean mismatched-source cosine. CKA compares the full set of source vectors across formats.

| Layer | Label alignment margin | Fact alignment margin | Label CKA | Fact CKA |
|---:|---:|---:|---:|---:|
| 0 | 0.001 [0.001, 0.002] | 0.149 [0.140, 0.159] | 0.697 [0.688, 0.706] | 1.000 [1.000, 1.000] |
| 4 | 0.036 [0.035, 0.036] | 0.172 [0.170, 0.175] | 0.839 [0.831, 0.846] | 0.998 [0.998, 0.999] |
| 8 | 0.025 [0.024, 0.025] | 0.146 [0.143, 0.148] | 0.833 [0.828, 0.838] | 0.995 [0.995, 0.995] |
| 12 | 0.026 [0.026, 0.027] | 0.154 [0.152, 0.156] | 0.670 [0.662, 0.678] | 0.983 [0.982, 0.985] |
| 16 | 0.015 [0.014, 0.015] | 0.135 [0.129, 0.142] | 0.736 [0.727, 0.746] | 0.981 [0.979, 0.983] |

## Within-condition binding geometry

Positive margins mean the state is more cosine-aligned with relevant than distractor sources.

| Condition | Layer | Pre-answer → source-fact margin | Pre-citation → source-label margin |
|---|---:|---:|---:|
| structured | 0 | -0.086 [-0.096, -0.076] | 0.002 [-0.002, 0.005] |
| structured | 4 | -0.003 [-0.009, 0.004] | -0.001 [-0.004, 0.002] |
| structured | 8 | 0.006 [-0.003, 0.015] | -0.001 [-0.003, 0.002] |
| structured | 12 | 0.016 [0.012, 0.019] | 0.004 [-0.001, 0.009] |
| structured | 16 | 0.005 [-0.003, 0.014] | 0.005 [0.001, 0.008] |
| random_compact | 0 | -0.086 [-0.096, -0.076] | -0.002 [-0.008, 0.004] |
| random_compact | 4 | -0.001 [-0.007, 0.006] | -0.005 [-0.009, -0.001] |
| random_compact | 8 | -0.000 [-0.009, 0.009] | -0.003 [-0.005, -0.001] |
| random_compact | 12 | 0.013 [0.009, 0.017] | 0.001 [-0.002, 0.005] |
| random_compact | 16 | 0.005 [-0.002, 0.012] | 0.005 [-0.001, 0.011] |
| uuid | 0 | -0.086 [-0.096, -0.076] | -0.000 [-0.004, 0.003] |
| uuid | 4 | -0.002 [-0.009, 0.004] | -0.001 [-0.005, 0.003] |
| uuid | 8 | 0.002 [-0.007, 0.011] | 0.002 [0.000, 0.003] |
| uuid | 12 | 0.018 [0.013, 0.022] | 0.004 [0.002, 0.006] |
| uuid | 16 | 0.004 [-0.004, 0.011] | 0.001 [-0.001, 0.003] |

## Exact-token reconstruction cost

NLL is mean negative log likelihood per teacher-forced answer or citation token; lower is easier.

| Condition | Mean identifier tokens | Citation sequence tokens | Answer NLL/token | Citation NLL/token | Citation total NLL |
|---|---:|---:|---:|---:|---:|
| structured | 4.000 [4.000, 4.000] | 12.000 [12.000, 12.000] | 8.000 [7.063, 8.934] | 1.981 [1.883, 2.080] | 23.772 [22.636, 24.967] |
| random_compact | 5.094 [5.067, 5.121] | 15.213 [14.975, 15.450] | 8.561 [7.539, 9.593] | 1.622 [1.511, 1.739] | 24.740 [22.898, 26.621] |
| uuid | 24.873 [24.777, 24.973] | 74.112 [73.362, 74.850] | 8.270 [7.405, 9.177] | 0.349 [0.328, 0.370] | 25.702 [24.242, 27.171] |

### Paired UUID cost

- `uuid_minus_structured_answer_nll`: 0.270 [-0.032, 0.590]
- `uuid_minus_structured_citation_nll`: -1.632 [-1.720, -1.544]
- `uuid_minus_structured_answer_total_nll`: 0.903 [0.305, 1.539]
- `uuid_minus_structured_citation_total_nll`: 1.930 [0.668, 3.147]

## Observable Stage 5 scratchpad behavior

These trace statistics are behavioral signals only, not mechanistic evidence.

| Identifier | Rows | Mentions exact relevant ID | Avoids all IDs | Shortened UUID prefix |
|---|---:|---:|---:|---:|
| numeric | 120 | 9.2% | 68.3% | — |
| random_compact | 120 | 12.5% | 66.7% | — |
| uuid | 120 | 8.3% | 72.5% | 0.8% |

## Checkpoint 6 interpretation

**Gate decision: proceed to targeted stage7.**

Structured-versus-UUID source-label relational geometry starts at CKA 0.697 and peaks at layer 6 (CKA 0.895). Source-fact CKA remains at least 0.970. At the final layer, question cosine is 0.983, pre-citation cosine is 0.598, and citation cosine is 0.372.

The paired UUID-minus-structured teacher-forced answer NLL difference is +0.270; the total citation NLL difference is +1.930. These likelihood measurements test literal reconstruction cost, while the representation curves test format-dependent state geometry.

The signature is correlational. If taken to Stage 7, patch or swap activations first at layers [4, 5, 6, 7, 8] and compare the late output region [11, 12, 13, 14, 15, 16]. Attention plots or probes alone are insufficient for the causal gate.

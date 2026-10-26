# Stage 6: explicit vs implicit symbolic compression

**Design:** 80 semantic examples × 3 identifier formats = 240 paired forward passes through `google/gemma-4-E4B-it`. The model has 42 transformer blocks plus the embedding state (43 stored layers) and hidden width 2560.

The same source order, source facts, question, answer, and relevant-source set are used across `[S1]`, compact arbitrary, and UUID conditions. Answer and citation states are teacher-forced so token spans align; they are representation measurements, not generated-answer accuracy estimates.

All intervals are 5,000-replicate paired bootstraps over complete semantic examples.

## Structured versus UUID representation similarity

| Layer | Source-label cosine | Source-fact cosine | Question cosine | Pre-answer cosine | Answer cosine | Pre-citation cosine | Citation cosine |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.737 [0.735, 0.738] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.756 [0.750, 0.761] |
| 10 | 0.855 [0.855, 0.856] | 0.997 [0.997, 0.997] | 1.000 [1.000, 1.000] | 0.999 [0.999, 1.000] | 0.998 [0.997, 0.998] | 1.000 [1.000, 1.000] | 0.917 [0.916, 0.918] |
| 21 | 0.785 [0.784, 0.786] | 0.992 [0.992, 0.992] | 0.998 [0.998, 0.998] | 0.993 [0.992, 0.994] | 0.986 [0.984, 0.988] | 0.993 [0.993, 0.993] | 0.899 [0.897, 0.900] |
| 32 | 0.900 [0.899, 0.900] | 0.997 [0.997, 0.998] | 0.999 [0.999, 0.999] | 0.995 [0.994, 0.996] | 0.996 [0.994, 0.997] | 0.961 [0.959, 0.963] | 0.933 [0.933, 0.934] |
| 42 | 0.263 [0.261, 0.265] | 0.977 [0.977, 0.978] | 0.991 [0.990, 0.991] | 0.962 [0.951, 0.973] | 0.960 [0.950, 0.969] | 0.497 [0.477, 0.517] | 0.512 [0.506, 0.517] |

## Source-identity geometry

Alignment margin is matched-source cosine minus the mean mismatched-source cosine. CKA compares the full set of source vectors across formats.

| Layer | Label alignment margin | Fact alignment margin | Label CKA | Fact CKA |
|---:|---:|---:|---:|---:|
| 0 | 0.001 [0.000, 0.001] | 0.083 [0.081, 0.085] | 0.435 [0.422, 0.449] | 1.000 [1.000, 1.000] |
| 10 | 0.003 [0.003, 0.003] | 0.020 [0.020, 0.020] | 0.849 [0.843, 0.855] | 0.997 [0.997, 0.998] |
| 21 | 0.011 [0.011, 0.012] | 0.044 [0.044, 0.045] | 0.899 [0.893, 0.905] | 0.995 [0.994, 0.995] |
| 32 | 0.002 [0.002, 0.002] | 0.016 [0.016, 0.017] | 0.863 [0.856, 0.869] | 0.992 [0.991, 0.992] |
| 42 | 0.008 [0.008, 0.008] | 0.185 [0.182, 0.188] | 0.829 [0.818, 0.839] | 0.995 [0.994, 0.995] |

## Within-condition binding geometry

Positive margins mean the state is more cosine-aligned with relevant than distractor sources.

| Condition | Layer | Pre-answer → source-fact margin | Pre-citation → source-label margin |
|---|---:|---:|---:|
| structured | 0 | -0.043 [-0.044, -0.042] | 0.001 [0.000, 0.002] |
| structured | 10 | -0.019 [-0.021, -0.017] | 0.001 [-0.000, 0.002] |
| structured | 21 | 0.004 [0.001, 0.006] | -0.001 [-0.004, 0.002] |
| structured | 32 | -0.002 [-0.005, 0.001] | 0.001 [0.000, 0.001] |
| structured | 42 | -0.049 [-0.055, -0.044] | -0.001 [-0.004, 0.002] |
| random_compact | 0 | -0.043 [-0.044, -0.042] | -0.001 [-0.004, 0.002] |
| random_compact | 10 | -0.019 [-0.021, -0.017] | 0.001 [-0.001, 0.002] |
| random_compact | 21 | 0.002 [0.000, 0.005] | -0.000 [-0.002, 0.001] |
| random_compact | 32 | -0.002 [-0.005, 0.001] | -0.001 [-0.002, 0.000] |
| random_compact | 42 | -0.047 [-0.053, -0.041] | -0.007 [-0.011, -0.003] |
| uuid | 0 | -0.043 [-0.044, -0.042] | -0.000 [-0.001, 0.001] |
| uuid | 10 | -0.019 [-0.021, -0.017] | 0.000 [-0.000, 0.001] |
| uuid | 21 | 0.004 [0.002, 0.006] | -0.001 [-0.001, -0.000] |
| uuid | 32 | -0.001 [-0.004, 0.002] | 0.002 [0.001, 0.002] |
| uuid | 42 | -0.050 [-0.055, -0.045] | -0.001 [-0.002, -0.000] |

## Exact-token reconstruction cost

NLL is mean negative log likelihood per teacher-forced answer or citation token; lower is easier.

| Condition | Mean identifier tokens | Citation sequence tokens | Answer NLL/token | Citation NLL/token | Citation total NLL |
|---|---:|---:|---:|---:|---:|
| structured | 4.475 [4.458, 4.492] | 13.525 [13.350, 13.688] | 6.655 [5.059, 8.280] | 3.689 [3.310, 4.073] | 49.698 [44.585, 54.982] |
| random_compact | 5.019 [4.986, 5.052] | 14.675 [14.450, 14.900] | 7.229 [5.556, 8.936] | 2.600 [2.313, 2.898] | 37.683 [33.809, 41.905] |
| uuid | 34.957 [34.840, 35.070] | 105.000 [104.375, 105.625] | 6.583 [5.036, 8.212] | 0.366 [0.320, 0.413] | 38.374 [33.551, 43.361] |

### Paired UUID cost

- `uuid_minus_structured_answer_nll`: -0.072 [-0.643, 0.529]
- `uuid_minus_structured_citation_nll`: -3.323 [-3.686, -2.976]
- `uuid_minus_structured_answer_total_nll`: -0.175 [-1.349, 1.022]
- `uuid_minus_structured_citation_total_nll`: -11.325 [-15.573, -7.279]

## Observable Stage 5 scratchpad behavior

These trace statistics are behavioral signals only, not mechanistic evidence.

| Identifier | Rows | Mentions exact relevant ID | Avoids all IDs | Shortened UUID prefix |
|---|---:|---:|---:|---:|
| numeric | 120 | 100.0% | 0.0% | — |
| random_compact | 120 | 100.0% | 0.0% | — |
| uuid | 120 | 100.0% | 0.0% | 23.3% |

## Checkpoint 6 interpretation

**Gate decision: proceed to targeted stage7.**

Structured-versus-UUID source-label relational geometry starts at CKA 0.435 and peaks at layer 25 (CKA 0.952). Source-fact CKA remains at least 0.979. At the final layer, question cosine is 0.991, pre-citation cosine is 0.497, and citation cosine is 0.512.

The paired UUID-minus-structured teacher-forced answer NLL difference is -0.072; the total citation NLL difference is -11.325. These likelihood measurements test literal reconstruction cost, while the representation curves test format-dependent state geometry.

The signature is correlational. If taken to Stage 7, patch or swap activations first at layers [23, 24, 25, 26, 27] and compare the late output region [29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42]. Attention plots or probes alone are insufficient for the causal gate.

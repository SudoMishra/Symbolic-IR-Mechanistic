# Stage 6: explicit vs implicit symbolic compression

**Design:** 80 semantic examples × 3 identifier formats = 240 paired forward passes through `google/gemma-4-E2B-it`. The model has 35 transformer blocks plus the embedding state (36 stored layers) and hidden width 1536.

The same source order, source facts, question, answer, and relevant-source set are used across `[S1]`, compact arbitrary, and UUID conditions. Answer and citation states are teacher-forced so token spans align; they are representation measurements, not generated-answer accuracy estimates.

All intervals are 5,000-replicate paired bootstraps over complete semantic examples.

## Structured versus UUID representation similarity

| Layer | Source-label cosine | Source-fact cosine | Question cosine | Pre-answer cosine | Answer cosine | Pre-citation cosine | Citation cosine |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.707 [0.705, 0.709] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.725 [0.718, 0.731] |
| 9 | 0.905 [0.905, 0.905] | 0.996 [0.995, 0.996] | 1.000 [1.000, 1.000] | 0.968 [0.936, 0.991] | 0.998 [0.997, 0.998] | 1.000 [1.000, 1.000] | 0.967 [0.967, 0.968] |
| 18 | 0.814 [0.812, 0.815] | 0.993 [0.992, 0.993] | 0.998 [0.998, 0.998] | 0.995 [0.995, 0.996] | 0.995 [0.995, 0.996] | 0.995 [0.995, 0.995] | 0.906 [0.905, 0.907] |
| 26 | 0.734 [0.733, 0.735] | 0.990 [0.990, 0.990] | 0.997 [0.996, 0.997] | 0.980 [0.978, 0.983] | 0.986 [0.984, 0.989] | 0.925 [0.922, 0.927] | 0.776 [0.774, 0.778] |
| 35 | 0.528 [0.522, 0.534] | 0.984 [0.983, 0.984] | 0.994 [0.993, 0.994] | 0.946 [0.935, 0.957] | 0.956 [0.943, 0.968] | 0.825 [0.815, 0.833] | 0.798 [0.793, 0.802] |

## Source-identity geometry

Alignment margin is matched-source cosine minus the mean mismatched-source cosine. CKA compares the full set of source vectors across formats.

| Layer | Label alignment margin | Fact alignment margin | Label CKA | Fact CKA |
|---:|---:|---:|---:|---:|
| 0 | 0.001 [0.000, 0.002] | 0.113 [0.110, 0.116] | 0.434 [0.421, 0.448] | 1.000 [1.000, 1.000] |
| 9 | 0.006 [0.006, 0.006] | 0.019 [0.018, 0.019] | 0.879 [0.874, 0.884] | 0.992 [0.991, 0.993] |
| 18 | 0.005 [0.005, 0.005] | 0.023 [0.022, 0.023] | 0.837 [0.832, 0.843] | 0.986 [0.985, 0.987] |
| 26 | 0.006 [0.006, 0.006] | 0.040 [0.039, 0.041] | 0.806 [0.799, 0.814] | 0.989 [0.988, 0.990] |
| 35 | 0.015 [0.014, 0.016] | 0.144 [0.141, 0.148] | 0.377 [0.367, 0.388] | 0.941 [0.935, 0.947] |

## Within-condition binding geometry

Positive margins mean the state is more cosine-aligned with relevant than distractor sources.

| Condition | Layer | Pre-answer → source-fact margin | Pre-citation → source-label margin |
|---|---:|---:|---:|
| structured | 0 | -0.040 [-0.044, -0.037] | 0.001 [0.000, 0.002] |
| structured | 9 | -0.010 [-0.012, -0.007] | -0.000 [-0.001, 0.001] |
| structured | 18 | -0.001 [-0.001, 0.000] | -0.001 [-0.002, 0.000] |
| structured | 26 | 0.006 [0.002, 0.009] | 0.004 [0.000, 0.007] |
| structured | 35 | -0.104 [-0.116, -0.091] | 0.004 [-0.008, 0.015] |
| random_compact | 0 | -0.040 [-0.044, -0.037] | -0.003 [-0.005, -0.000] |
| random_compact | 9 | -0.006 [-0.009, -0.004] | 0.001 [-0.000, 0.002] |
| random_compact | 18 | -0.005 [-0.006, -0.004] | -0.001 [-0.002, 0.000] |
| random_compact | 26 | 0.009 [0.006, 0.012] | 0.007 [0.005, 0.009] |
| random_compact | 35 | -0.089 [-0.105, -0.075] | 0.005 [-0.004, 0.013] |
| uuid | 0 | -0.040 [-0.044, -0.037] | -0.000 [-0.001, 0.000] |
| uuid | 9 | -0.010 [-0.012, -0.009] | 0.000 [-0.001, 0.001] |
| uuid | 18 | -0.005 [-0.006, -0.004] | -0.002 [-0.005, 0.001] |
| uuid | 26 | 0.008 [0.005, 0.011] | 0.003 [0.002, 0.005] |
| uuid | 35 | -0.094 [-0.111, -0.077] | -0.014 [-0.029, 0.001] |

## Exact-token reconstruction cost

NLL is mean negative log likelihood per teacher-forced answer or citation token; lower is easier.

| Condition | Mean identifier tokens | Citation sequence tokens | Answer NLL/token | Citation NLL/token | Citation total NLL |
|---|---:|---:|---:|---:|---:|
| structured | 4.475 [4.458, 4.492] | 13.525 [13.350, 13.688] | 3.481 [2.694, 4.297] | 3.184 [2.931, 3.442] | 43.234 [39.661, 46.912] |
| random_compact | 5.019 [4.986, 5.052] | 14.675 [14.450, 14.900] | 4.176 [3.294, 5.111] | 2.496 [2.304, 2.687] | 36.576 [33.780, 39.393] |
| uuid | 34.957 [34.840, 35.070] | 105.000 [104.375, 105.625] | 4.137 [3.288, 5.079] | 0.416 [0.385, 0.448] | 43.686 [40.387, 46.855] |

### Paired UUID cost

- `uuid_minus_structured_answer_nll`: 0.656 [0.208, 1.137]
- `uuid_minus_structured_citation_nll`: -2.768 [-3.013, -2.510]
- `uuid_minus_structured_answer_total_nll`: 1.689 [0.706, 2.741]
- `uuid_minus_structured_citation_total_nll`: 0.451 [-3.887, 4.665]

## Observable Stage 5 scratchpad behavior

These trace statistics are behavioral signals only, not mechanistic evidence.

| Identifier | Rows | Mentions exact relevant ID | Avoids all IDs | Shortened UUID prefix |
|---|---:|---:|---:|---:|
| numeric | 200 | 100.0% | 0.0% | — |
| random_compact | 200 | 97.0% | 3.0% | — |
| uuid | 200 | 99.5% | 0.5% | 24.0% |

## Checkpoint 6 interpretation

**Gate decision: proceed to targeted stage7.**

Structured-versus-UUID source-label relational geometry starts at CKA 0.434 and peaks at layer 15 (CKA 0.931). Source-fact CKA remains at least 0.941. At the final layer, question cosine is 0.994, pre-citation cosine is 0.825, and citation cosine is 0.798.

The paired UUID-minus-structured teacher-forced answer NLL difference is +0.656; the total citation NLL difference is +0.451. These likelihood measurements test literal reconstruction cost, while the representation curves test format-dependent state geometry.

The signature is correlational. If taken to Stage 7, patch or swap activations first at layers [13, 14, 15, 16, 17] and compare the late output region [24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]. Attention plots or probes alone are insufficient for the causal gate.

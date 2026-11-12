# Stage 6: explicit vs implicit symbolic compression

**Design:** 80 semantic examples × 3 identifier formats = 240 paired forward passes through `Qwen/Qwen3.5-2B`. The model has 24 transformer blocks plus the embedding state (25 stored layers) and hidden width 2048.

The same source order, source facts, question, answer, and relevant-source set are used across `[S1]`, compact arbitrary, and UUID conditions. Answer and citation states are teacher-forced so token spans align; they are representation measurements, not generated-answer accuracy estimates.

All intervals are 5,000-replicate paired bootstraps over complete semantic examples.

## Structured versus UUID representation similarity

| Layer | Source-label cosine | Source-fact cosine | Question cosine | Pre-answer cosine | Answer cosine | Pre-citation cosine | Citation cosine |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.722 [0.719, 0.725] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.846 [0.841, 0.851] |
| 6 | 0.607 [0.606, 0.609] | 0.994 [0.994, 0.994] | 0.999 [0.999, 0.999] | 0.997 [0.997, 0.997] | 0.995 [0.995, 0.996] | 0.998 [0.997, 0.998] | 0.802 [0.800, 0.803] |
| 12 | 0.614 [0.613, 0.615] | 0.978 [0.977, 0.978] | 0.991 [0.991, 0.992] | 0.991 [0.990, 0.992] | 0.960 [0.957, 0.964] | 0.992 [0.991, 0.992] | 0.750 [0.748, 0.752] |
| 18 | 0.674 [0.673, 0.675] | 0.983 [0.982, 0.983] | 0.998 [0.998, 0.998] | 0.977 [0.974, 0.981] | 0.982 [0.979, 0.985] | 0.907 [0.904, 0.910] | 0.686 [0.684, 0.689] |
| 24 | 0.579 [0.577, 0.580] | 0.991 [0.991, 0.991] | 0.998 [0.998, 0.998] | 0.979 [0.975, 0.983] | 0.975 [0.971, 0.979] | 0.779 [0.766, 0.790] | 0.586 [0.582, 0.590] |

## Source-identity geometry

Alignment margin is matched-source cosine minus the mean mismatched-source cosine. CKA compares the full set of source vectors across formats.

| Layer | Label alignment margin | Fact alignment margin | Label CKA | Fact CKA |
|---:|---:|---:|---:|---:|
| 0 | 0.001 [0.000, 0.002] | 0.085 [0.083, 0.088] | 0.316 [0.301, 0.332] | 1.000 [1.000, 1.000] |
| 6 | 0.011 [0.011, 0.012] | 0.077 [0.075, 0.078] | 0.848 [0.842, 0.853] | 0.998 [0.998, 0.998] |
| 12 | 0.029 [0.028, 0.029] | 0.114 [0.112, 0.117] | 0.897 [0.893, 0.901] | 0.994 [0.993, 0.994] |
| 18 | 0.014 [0.014, 0.015] | 0.067 [0.065, 0.068] | 0.881 [0.876, 0.886] | 0.987 [0.986, 0.988] |
| 24 | 0.009 [0.009, 0.010] | 0.061 [0.059, 0.064] | 0.866 [0.861, 0.870] | 0.993 [0.993, 0.994] |

## Within-condition binding geometry

Positive margins mean the state is more cosine-aligned with relevant than distractor sources.

| Condition | Layer | Pre-answer → source-fact margin | Pre-citation → source-label margin |
|---|---:|---:|---:|
| structured | 0 | -0.095 [-0.098, -0.091] | 0.009 [-0.001, 0.018] |
| structured | 6 | -0.052 [-0.053, -0.050] | -0.001 [-0.005, 0.002] |
| structured | 12 | -0.004 [-0.008, 0.000] | 0.005 [0.000, 0.010] |
| structured | 18 | 0.016 [0.015, 0.018] | 0.004 [0.001, 0.007] |
| structured | 24 | 0.006 [-0.000, 0.013] | 0.004 [-0.001, 0.008] |
| random_compact | 0 | -0.095 [-0.098, -0.091] | -0.012 [-0.036, 0.012] |
| random_compact | 6 | -0.055 [-0.057, -0.054] | -0.003 [-0.008, 0.002] |
| random_compact | 12 | -0.005 [-0.008, -0.002] | 0.003 [-0.000, 0.006] |
| random_compact | 18 | 0.018 [0.017, 0.020] | 0.005 [0.002, 0.008] |
| random_compact | 24 | 0.008 [0.000, 0.016] | 0.008 [0.005, 0.012] |
| uuid | 0 | -0.095 [-0.098, -0.092] | 0.000 [-0.002, 0.002] |
| uuid | 6 | -0.056 [-0.057, -0.055] | -0.002 [-0.003, -0.000] |
| uuid | 12 | -0.008 [-0.011, -0.005] | 0.001 [-0.000, 0.002] |
| uuid | 18 | 0.017 [0.015, 0.019] | 0.004 [0.003, 0.005] |
| uuid | 24 | 0.004 [-0.003, 0.011] | 0.002 [0.000, 0.004] |

## Exact-token reconstruction cost

NLL is mean negative log likelihood per teacher-forced answer or citation token; lower is easier.

| Condition | Mean identifier tokens | Citation sequence tokens | Answer NLL/token | Citation NLL/token | Citation total NLL |
|---|---:|---:|---:|---:|---:|
| structured | 3.475 [3.458, 3.492] | 13.463 [13.287, 13.637] | 1.487 [1.198, 1.787] | 0.762 [0.707, 0.817] | 10.200 [9.466, 10.922] |
| random_compact | 4.757 [4.723, 4.789] | 15.075 [14.863, 15.287] | 1.565 [1.256, 1.881] | 0.677 [0.624, 0.731] | 10.162 [9.381, 10.988] |
| uuid | 33.431 [33.303, 33.553] | 101.275 [100.575, 101.975] | 1.463 [1.172, 1.768] | 0.110 [0.103, 0.116] | 11.100 [10.472, 11.709] |

### Paired UUID cost

- `uuid_minus_structured_answer_nll`: -0.024 [-0.083, 0.028]
- `uuid_minus_structured_citation_nll`: -0.653 [-0.705, -0.599]
- `uuid_minus_structured_answer_total_nll`: -0.027 [-0.148, 0.078]
- `uuid_minus_structured_citation_total_nll`: 0.899 [0.190, 1.628]

## Observable Stage 5 scratchpad behavior

These trace statistics are behavioral signals only, not mechanistic evidence.

| Identifier | Rows | Mentions exact relevant ID | Avoids all IDs | Shortened UUID prefix |
|---|---:|---:|---:|---:|
| numeric | 200 | 94.0% | 6.0% | — |
| random_compact | 200 | 96.0% | 3.5% | — |
| uuid | 200 | 87.0% | 12.0% | 11.0% |

## Checkpoint 6 interpretation

**Gate decision: proceed to targeted stage7.**

Structured-versus-UUID source-label relational geometry starts at CKA 0.316 and peaks at layer 16 (CKA 0.908). Source-fact CKA remains at least 0.985. At the final layer, question cosine is 0.998, pre-citation cosine is 0.779, and citation cosine is 0.586.

The paired UUID-minus-structured teacher-forced answer NLL difference is -0.024; the total citation NLL difference is +0.899. These likelihood measurements test literal reconstruction cost, while the representation curves test format-dependent state geometry.

The signature is correlational. If taken to Stage 7, patch or swap activations first at layers [14, 15, 16, 17, 18] and compare the late output region [16, 17, 18, 19, 20, 21, 22, 23, 24]. Attention plots or probes alone are insufficient for the causal gate.

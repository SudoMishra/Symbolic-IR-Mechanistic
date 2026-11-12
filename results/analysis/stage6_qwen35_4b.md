# Stage 6: explicit vs implicit symbolic compression

**Design:** 80 semantic examples × 3 identifier formats = 240 paired forward passes through `Qwen/Qwen3.5-4B`. The model has 32 transformer blocks plus the embedding state (33 stored layers) and hidden width 2560.

The same source order, source facts, question, answer, and relevant-source set are used across `[S1]`, compact arbitrary, and UUID conditions. Answer and citation states are teacher-forced so token spans align; they are representation measurements, not generated-answer accuracy estimates.

All intervals are 5,000-replicate paired bootstraps over complete semantic examples.

## Structured versus UUID representation similarity

| Layer | Source-label cosine | Source-fact cosine | Question cosine | Pre-answer cosine | Answer cosine | Pre-citation cosine | Citation cosine |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.749 [0.746, 0.752] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.851 [0.846, 0.856] |
| 8 | 0.739 [0.738, 0.740] | 0.994 [0.994, 0.994] | 0.998 [0.998, 0.998] | 0.996 [0.995, 0.996] | 0.987 [0.985, 0.989] | 0.996 [0.996, 0.997] | 0.892 [0.890, 0.893] |
| 16 | 0.726 [0.725, 0.727] | 0.986 [0.986, 0.986] | 0.996 [0.995, 0.996] | 0.990 [0.988, 0.991] | 0.972 [0.967, 0.977] | 0.983 [0.982, 0.983] | 0.869 [0.867, 0.871] |
| 24 | 0.785 [0.784, 0.786] | 0.985 [0.984, 0.985] | 0.998 [0.998, 0.998] | 0.979 [0.975, 0.982] | 0.977 [0.973, 0.981] | 0.847 [0.843, 0.852] | 0.776 [0.773, 0.779] |
| 32 | 0.585 [0.583, 0.587] | 0.991 [0.991, 0.991] | 0.998 [0.998, 0.998] | 0.985 [0.983, 0.987] | 0.978 [0.976, 0.980] | 0.733 [0.721, 0.744] | 0.606 [0.603, 0.610] |

## Source-identity geometry

Alignment margin is matched-source cosine minus the mean mismatched-source cosine. CKA compares the full set of source vectors across formats.

| Layer | Label alignment margin | Fact alignment margin | Label CKA | Fact CKA |
|---:|---:|---:|---:|---:|
| 0 | 0.001 [0.000, 0.001] | 0.083 [0.081, 0.086] | 0.330 [0.314, 0.346] | 1.000 [1.000, 1.000] |
| 8 | 0.016 [0.016, 0.017] | 0.098 [0.096, 0.100] | 0.910 [0.907, 0.914] | 0.998 [0.998, 0.998] |
| 16 | 0.027 [0.027, 0.028] | 0.101 [0.099, 0.103] | 0.917 [0.914, 0.920] | 0.996 [0.996, 0.996] |
| 24 | 0.014 [0.013, 0.014] | 0.078 [0.076, 0.080] | 0.851 [0.846, 0.856] | 0.990 [0.989, 0.991] |
| 32 | 0.007 [0.007, 0.008] | 0.075 [0.073, 0.077] | 0.885 [0.880, 0.891] | 0.997 [0.997, 0.997] |

## Within-condition binding geometry

Positive margins mean the state is more cosine-aligned with relevant than distractor sources.

| Condition | Layer | Pre-answer → source-fact margin | Pre-citation → source-label margin |
|---|---:|---:|---:|
| structured | 0 | -0.080 [-0.084, -0.075] | 0.007 [-0.000, 0.015] |
| structured | 8 | -0.055 [-0.058, -0.052] | -0.001 [-0.002, 0.000] |
| structured | 16 | -0.016 [-0.021, -0.010] | -0.000 [-0.002, 0.002] |
| structured | 24 | 0.014 [0.011, 0.018] | 0.004 [0.002, 0.006] |
| structured | 32 | 0.018 [0.014, 0.022] | 0.002 [-0.003, 0.007] |
| random_compact | 0 | -0.080 [-0.085, -0.075] | -0.009 [-0.030, 0.011] |
| random_compact | 8 | -0.059 [-0.062, -0.056] | 0.002 [-0.003, 0.006] |
| random_compact | 16 | -0.013 [-0.019, -0.007] | 0.002 [-0.001, 0.004] |
| random_compact | 24 | 0.015 [0.012, 0.018] | 0.004 [0.000, 0.007] |
| random_compact | 32 | 0.017 [0.013, 0.020] | 0.005 [0.002, 0.009] |
| uuid | 0 | -0.080 [-0.085, -0.075] | 0.000 [-0.001, 0.002] |
| uuid | 8 | -0.055 [-0.057, -0.053] | 0.000 [-0.001, 0.001] |
| uuid | 16 | -0.015 [-0.020, -0.010] | 0.001 [-0.000, 0.002] |
| uuid | 24 | 0.014 [0.011, 0.017] | 0.005 [0.004, 0.006] |
| uuid | 32 | 0.022 [0.018, 0.025] | 0.001 [-0.000, 0.002] |

## Exact-token reconstruction cost

NLL is mean negative log likelihood per teacher-forced answer or citation token; lower is easier.

| Condition | Mean identifier tokens | Citation sequence tokens | Answer NLL/token | Citation NLL/token | Citation total NLL |
|---|---:|---:|---:|---:|---:|
| structured | 3.475 [3.458, 3.492] | 13.463 [13.287, 13.637] | 1.015 [0.791, 1.251] | 0.381 [0.344, 0.420] | 5.113 [4.613, 5.636] |
| random_compact | 4.757 [4.723, 4.789] | 15.075 [14.863, 15.287] | 0.941 [0.723, 1.168] | 0.361 [0.321, 0.404] | 5.429 [4.846, 6.050] |
| uuid | 33.431 [33.303, 33.553] | 101.275 [100.575, 101.975] | 0.919 [0.703, 1.155] | 0.052 [0.046, 0.058] | 5.239 [4.671, 5.838] |

### Paired UUID cost

- `uuid_minus_structured_answer_nll`: -0.097 [-0.170, -0.027]
- `uuid_minus_structured_citation_nll`: -0.330 [-0.365, -0.296]
- `uuid_minus_structured_answer_total_nll`: -0.204 [-0.349, -0.072]
- `uuid_minus_structured_citation_total_nll`: 0.126 [-0.340, 0.610]

## Observable Stage 5 scratchpad behavior

These trace statistics are behavioral signals only, not mechanistic evidence.

| Identifier | Rows | Mentions exact relevant ID | Avoids all IDs | Shortened UUID prefix |
|---|---:|---:|---:|---:|
| numeric | 200 | 100.0% | 0.0% | — |
| random_compact | 200 | 99.0% | 0.0% | — |
| uuid | 200 | 96.5% | 0.5% | 22.5% |

## Checkpoint 6 interpretation

**Gate decision: proceed to targeted stage7.**

Structured-versus-UUID source-label relational geometry starts at CKA 0.330 and peaks at layer 17 (CKA 0.919). Source-fact CKA remains at least 0.984. At the final layer, question cosine is 0.998, pre-citation cosine is 0.733, and citation cosine is 0.606.

The paired UUID-minus-structured teacher-forced answer NLL difference is -0.097; the total citation NLL difference is +0.126. These likelihood measurements test literal reconstruction cost, while the representation curves test format-dependent state geometry.

The signature is correlational. If taken to Stage 7, patch or swap activations first at layers [15, 16, 17, 18, 19] and compare the late output region [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]. Attention plots or probes alone are insufficient for the causal gate.

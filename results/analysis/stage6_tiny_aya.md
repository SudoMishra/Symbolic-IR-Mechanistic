# Stage 6: explicit vs implicit symbolic compression

**Design:** 80 semantic examples × 3 identifier formats = 240 paired forward passes through `CohereLabs/tiny-aya-global`. The model has 36 transformer blocks plus the embedding state (37 stored layers) and hidden width 2048.

The same source order, source facts, question, answer, and relevant-source set are used across `[S1]`, compact arbitrary, and UUID conditions. Answer and citation states are teacher-forced so token spans align; they are representation measurements, not generated-answer accuracy estimates.

All intervals are 5,000-replicate paired bootstraps over complete semantic examples.

## Structured versus UUID representation similarity

| Layer | Source-label cosine | Source-fact cosine | Question cosine | Pre-answer cosine | Answer cosine | Pre-citation cosine | Citation cosine |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.846 [0.845, 0.847] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.854 [0.853, 0.855] |
| 9 | 0.319 [0.318, 0.320] | 0.963 [0.963, 0.963] | 0.994 [0.994, 0.994] | 0.987 [0.987, 0.988] | 0.966 [0.962, 0.969] | 0.994 [0.993, 0.994] | 0.471 [0.468, 0.473] |
| 18 | 0.372 [0.371, 0.374] | 0.921 [0.914, 0.928] | 0.989 [0.988, 0.990] | 0.979 [0.978, 0.980] | 0.943 [0.934, 0.951] | 0.980 [0.980, 0.981] | 0.441 [0.437, 0.445] |
| 27 | 0.487 [0.486, 0.489] | 0.947 [0.942, 0.952] | 0.995 [0.994, 0.995] | 0.965 [0.960, 0.969] | 0.977 [0.975, 0.979] | 0.780 [0.776, 0.785] | 0.449 [0.444, 0.453] |
| 36 | 0.233 [0.231, 0.235] | 0.982 [0.982, 0.983] | 0.990 [0.990, 0.991] | 0.941 [0.929, 0.952] | 0.966 [0.963, 0.970] | 0.435 [0.425, 0.445] | 0.447 [0.443, 0.452] |

## Source-identity geometry

Alignment margin is matched-source cosine minus the mean mismatched-source cosine. CKA compares the full set of source vectors across formats.

| Layer | Label alignment margin | Fact alignment margin | Label CKA | Fact CKA |
|---:|---:|---:|---:|---:|
| 0 | 0.000 [0.000, 0.001] | 0.031 [0.028, 0.035] | 0.413 [0.397, 0.428] | 1.000 [1.000, 1.000] |
| 9 | 0.024 [0.024, 0.025] | 0.197 [0.194, 0.201] | 0.836 [0.825, 0.847] | 0.999 [0.999, 0.999] |
| 18 | 0.040 [0.040, 0.041] | 0.208 [0.203, 0.214] | 0.800 [0.794, 0.806] | 0.614 [0.538, 0.691] |
| 27 | 0.025 [0.025, 0.026] | 0.127 [0.124, 0.131] | 0.766 [0.759, 0.772] | 0.718 [0.661, 0.775] |
| 36 | 0.011 [0.011, 0.011] | 0.141 [0.138, 0.144] | 0.888 [0.883, 0.893] | 0.997 [0.997, 0.997] |

## Within-condition binding geometry

Positive margins mean the state is more cosine-aligned with relevant than distractor sources.

| Condition | Layer | Pre-answer → source-fact margin | Pre-citation → source-label margin |
|---|---:|---:|---:|
| structured | 0 | -0.022 [-0.029, -0.016] | 0.002 [-0.001, 0.004] |
| structured | 9 | -0.019 [-0.026, -0.013] | 0.001 [-0.001, 0.002] |
| structured | 18 | 0.068 [0.054, 0.083] | 0.005 [-0.001, 0.011] |
| structured | 27 | 0.058 [0.051, 0.066] | 0.004 [0.002, 0.006] |
| structured | 36 | 0.045 [0.037, 0.053] | 0.002 [-0.000, 0.005] |
| random_compact | 0 | -0.022 [-0.029, -0.016] | 0.000 [-0.003, 0.004] |
| random_compact | 9 | -0.022 [-0.027, -0.016] | 0.004 [0.002, 0.006] |
| random_compact | 18 | 0.062 [0.048, 0.077] | 0.004 [-0.000, 0.009] |
| random_compact | 27 | 0.060 [0.054, 0.067] | 0.009 [0.006, 0.012] |
| random_compact | 36 | 0.037 [0.029, 0.045] | 0.000 [-0.005, 0.005] |
| uuid | 0 | -0.022 [-0.029, -0.016] | 0.001 [-0.002, 0.003] |
| uuid | 9 | -0.025 [-0.029, -0.021] | 0.000 [-0.001, 0.002] |
| uuid | 18 | 0.071 [0.059, 0.083] | 0.004 [0.001, 0.008] |
| uuid | 27 | 0.060 [0.053, 0.066] | 0.012 [0.010, 0.014] |
| uuid | 36 | 0.032 [0.024, 0.041] | 0.000 [-0.003, 0.003] |

## Exact-token reconstruction cost

NLL is mean negative log likelihood per teacher-forced answer or citation token; lower is easier.

| Condition | Mean identifier tokens | Citation sequence tokens | Answer NLL/token | Citation NLL/token | Citation total NLL |
|---|---:|---:|---:|---:|---:|
| structured | 3.000 [3.000, 3.000] | 12.000 [12.000, 12.000] | 3.200 [2.501, 3.909] | 1.151 [1.081, 1.219] | 13.810 [13.001, 14.617] |
| random_compact | 4.745 [4.714, 4.775] | 14.125 [13.912, 14.338] | 3.019 [2.385, 3.698] | 1.183 [1.094, 1.273] | 16.661 [15.389, 17.918] |
| uuid | 24.395 [24.296, 24.496] | 72.963 [72.200, 73.700] | 2.924 [2.273, 3.596] | 0.249 [0.232, 0.265] | 18.065 [16.935, 19.200] |

### Paired UUID cost

- `uuid_minus_structured_answer_nll`: -0.275 [-0.445, -0.118]
- `uuid_minus_structured_citation_nll`: -0.902 [-0.961, -0.840]
- `uuid_minus_structured_answer_total_nll`: -0.258 [-0.449, -0.067]
- `uuid_minus_structured_citation_total_nll`: 4.254 [3.299, 5.258]

## Observable Stage 5 scratchpad behavior

These trace statistics are behavioral signals only, not mechanistic evidence.

| Identifier | Rows | Mentions exact relevant ID | Avoids all IDs | Shortened UUID prefix |
|---|---:|---:|---:|---:|
| numeric | 200 | 72.5% | 27.5% | — |
| random_compact | 200 | 50.5% | 49.0% | — |
| uuid | 200 | 53.5% | 45.5% | 15.0% |

## Checkpoint 6 interpretation

**Gate decision: no clear stage7 gate.**

Structured-versus-UUID source-label relational geometry starts at CKA 0.413 and peaks at layer 12 (CKA 0.915). Source-fact CKA remains at least 0.610. At the final layer, question cosine is 0.990, pre-citation cosine is 0.435, and citation cosine is 0.447.

The paired UUID-minus-structured teacher-forced answer NLL difference is -0.275; the total citation NLL difference is +4.254. These likelihood measurements test literal reconstruction cost, while the representation curves test format-dependent state geometry.

The signature is correlational. If taken to Stage 7, patch or swap activations first at layers [10, 11, 12, 13, 14] and compare the late output region [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]. Attention plots or probes alone are insufficient for the causal gate.

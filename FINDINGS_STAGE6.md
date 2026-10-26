# Stage 6: explicit vs implicit symbolic compression

**Design:** 80 semantic examples × 3 identifier formats = 240 paired forward passes through `Qwen/Qwen2.5-1.5B-Instruct`. The model has 28 transformer blocks plus the embedding state (29 stored layers) and hidden width 1536.

The same source order, source facts, question, answer, and relevant-source set are used across `[S1]`, compact arbitrary, and UUID conditions. Answer and citation states are teacher-forced so token spans align; they are representation measurements, not generated-answer accuracy estimates.

All intervals are 5,000-replicate paired bootstraps over complete semantic examples.

## Structured versus UUID representation similarity

| Layer | Source-label cosine | Source-fact cosine | Question cosine | Pre-answer cosine | Answer cosine | Pre-citation cosine | Citation cosine |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.669 [0.666, 0.673] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.803 [0.797, 0.810] |
| 7 | 0.627 [0.626, 0.628] | 0.993 [0.993, 0.994] | 0.999 [0.999, 0.999] | 0.998 [0.998, 0.998] | 0.996 [0.996, 0.997] | 0.999 [0.999, 0.999] | 0.694 [0.692, 0.697] |
| 14 | 0.598 [0.597, 0.599] | 0.978 [0.977, 0.978] | 0.998 [0.998, 0.998] | 0.994 [0.993, 0.995] | 0.994 [0.994, 0.995] | 0.993 [0.992, 0.993] | 0.634 [0.631, 0.638] |
| 21 | 0.544 [0.543, 0.545] | 0.980 [0.980, 0.981] | 0.996 [0.995, 0.996] | 0.976 [0.974, 0.979] | 0.983 [0.981, 0.985] | 0.932 [0.928, 0.935] | 0.616 [0.613, 0.619] |
| 28 | 0.564 [0.560, 0.567] | 0.999 [0.999, 0.999] | 0.999 [0.999, 0.999] | 0.985 [0.982, 0.988] | 0.987 [0.984, 0.989] | 0.828 [0.822, 0.835] | 0.721 [0.717, 0.726] |

## Source-identity geometry

Alignment margin is matched-source cosine minus the mean mismatched-source cosine. CKA compares the full set of source vectors across formats.

| Layer | Label alignment margin | Fact alignment margin | Label CKA | Fact CKA |
|---:|---:|---:|---:|---:|
| 0 | 0.001 [0.000, 0.001] | 0.103 [0.100, 0.105] | 0.325 [0.310, 0.340] | 1.000 [1.000, 1.000] |
| 7 | 0.006 [0.006, 0.007] | 0.082 [0.080, 0.084] | 0.682 [0.669, 0.695] | 0.999 [0.998, 0.999] |
| 14 | 0.015 [0.014, 0.015] | 0.081 [0.080, 0.083] | 0.696 [0.684, 0.708] | 0.969 [0.967, 0.971] |
| 21 | 0.019 [0.018, 0.019] | 0.097 [0.096, 0.099] | 0.667 [0.656, 0.677] | 0.982 [0.981, 0.983] |
| 28 | 0.001 [0.001, 0.001] | 0.020 [0.019, 0.021] | 0.743 [0.731, 0.754] | 0.992 [0.991, 0.992] |

## Within-condition binding geometry

Positive margins mean the state is more cosine-aligned with relevant than distractor sources.

| Condition | Layer | Pre-answer → source-fact margin | Pre-citation → source-label margin |
|---|---:|---:|---:|
| structured | 0 | -0.095 [-0.098, -0.092] | 0.008 [-0.001, 0.016] |
| structured | 7 | -0.049 [-0.050, -0.047] | -0.001 [-0.003, 0.000] |
| structured | 14 | -0.006 [-0.007, -0.004] | 0.002 [-0.001, 0.005] |
| structured | 21 | 0.013 [0.009, 0.018] | 0.000 [-0.004, 0.004] |
| structured | 28 | -0.061 [-0.067, -0.054] | -0.001 [-0.005, 0.002] |
| random_compact | 0 | -0.095 [-0.098, -0.092] | -0.012 [-0.035, 0.010] |
| random_compact | 7 | -0.053 [-0.054, -0.051] | 0.003 [-0.000, 0.006] |
| random_compact | 14 | -0.012 [-0.014, -0.010] | 0.002 [-0.000, 0.005] |
| random_compact | 21 | 0.012 [0.007, 0.017] | 0.005 [0.002, 0.009] |
| random_compact | 28 | -0.059 [-0.065, -0.053] | 0.003 [-0.001, 0.007] |
| uuid | 0 | -0.095 [-0.098, -0.092] | 0.000 [-0.001, 0.002] |
| uuid | 7 | -0.053 [-0.055, -0.051] | 0.000 [-0.001, 0.001] |
| uuid | 14 | -0.006 [-0.008, -0.004] | 0.000 [-0.002, 0.003] |
| uuid | 21 | 0.012 [0.007, 0.017] | 0.004 [0.001, 0.007] |
| uuid | 28 | -0.064 [-0.072, -0.057] | 0.003 [-0.002, 0.008] |

## Exact-token reconstruction cost

NLL is mean negative log likelihood per teacher-forced answer or citation token; lower is easier.

| Condition | Mean identifier tokens | Citation sequence tokens | Answer NLL/token | Citation NLL/token | Citation total NLL |
|---|---:|---:|---:|---:|---:|
| structured | 3.475 [3.458, 3.492] | 13.463 [13.287, 13.637] | 1.535 [1.190, 1.922] | 1.392 [1.314, 1.469] | 18.675 [17.669, 19.709] |
| random_compact | 4.759 [4.725, 4.792] | 15.088 [14.875, 15.300] | 1.570 [1.234, 1.896] | 1.253 [1.185, 1.323] | 18.809 [17.781, 19.793] |
| uuid | 33.431 [33.303, 33.553] | 101.275 [100.575, 101.975] | 1.546 [1.192, 1.923] | 0.164 [0.155, 0.174] | 16.630 [15.741, 17.548] |

### Paired UUID cost

- `uuid_minus_structured_answer_nll`: 0.011 [-0.119, 0.139]
- `uuid_minus_structured_citation_nll`: -1.227 [-1.300, -1.153]
- `uuid_minus_structured_answer_total_nll`: -0.038 [-0.289, 0.212]
- `uuid_minus_structured_citation_total_nll`: -2.045 [-3.115, -0.949]

## Observable Stage 5 scratchpad behavior

These trace statistics are behavioral signals only, not mechanistic evidence.

| Identifier | Rows | Mentions exact relevant ID | Avoids all IDs | Shortened UUID prefix |
|---|---:|---:|---:|---:|
| numeric | 400 | 0.8% | 99.2% | — |
| random_compact | 400 | 0.0% | 100.0% | — |
| uuid | 400 | 0.5% | 98.8% | 0.0% |

## Checkpoint 6 interpretation

**Gate decision: proceed to targeted Stage 7 causal interventions.**

The representation-level signature matches the roadmap qualitatively. Structured and UUID label embeddings begin with different geometry (label CKA 0.325), but their source-label relational geometry converges through the early/middle stack and peaks at layer 13 (CKA 0.858). Source-fact CKA remains at least 0.969, and question/pre-answer cosine remains above 0.975, showing that semantic task state is largely invariant to surface form. Divergence returns near output: structured-versus-UUID pre-citation cosine falls to 0.828 at layer 28 while citation-token cosine is 0.721.

Teacher-forced likelihood does not show a UUID reconstruction penalty: answer NLL is unchanged and UUID citation tokens have lower per-token and total NLL despite a much longer sequence. Together with Stage 5's lack of Qwen recovery when citation reproduction is removed, this points away from simple token copying and toward binding/retrieval or free-running trajectory errors.

The signature is correlational. Stage 7 should first patch or swap activations around layers 10–14, where label geometry converges and changes abruptly, then test layers 20–28 where pre-citation states become format-specific. Attention plots or probes alone are insufficient for the causal gate.

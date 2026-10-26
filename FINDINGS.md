# Symbolic identifier experiment findings

## Executive result

For Qwen2.5-1.5B-Instruct Q4_K_M, compact identifiers substantially reduced token cost and improved source binding relative to UUIDs. The evidence points primarily to length/copy burden, while delimiter choice strongly affected literal output formatting. Answer content was comparatively stable.

The confirmatory Stage 1 statistics are in [FINDINGS_STAGE1.md](FINDINGS_STAGE1.md). The tables below add the exploratory identifier-family sweep and token-matched control.

## Stage 2 exploratory family sweep

Twenty paired examples were run per cell, so these are directional estimates.

| Sources | Identifier | ID tokens | Answer content | Strict citation | Exact binding | Input tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|
| 5 | numeric | 3.00 | 100.0% | 95.0% | 95.0% | 234.3 | 1.73s |
| 5 | structured | 3.00 | 100.0% | 60.0% | 100.0% | 234.3 | 1.73s |
| 5 | semantic | 4.00 | 100.0% | 40.0% | 100.0% | 239.3 | 1.81s |
| 5 | random_compact | 4.76 | 100.0% | 90.0% | 95.0% | 243.2 | 1.87s |
| 5 | hex6 | 7.14 | 100.0% | 85.0% | 85.0% | 255.1 | 2.07s |
| 5 | hex32 | 29.76 | 100.0% | 70.0% | 90.0% | 368.1 | 3.97s |
| 5 | uuid | 32.85 | 100.0% | 70.0% | 85.0% | 383.6 | 4.22s |
| 20 | numeric | 3.55 | 80.0% | 85.0% | 85.0% | 639.1 | 5.31s |
| 20 | structured | 3.55 | 85.0% | 0.0% | 55.0% | 639.1 | 5.32s |
| 20 | semantic | 4.55 | 85.0% | 5.0% | 80.0% | 659.1 | 5.53s |
| 20 | random_compact | 4.79 | 80.0% | 65.0% | 70.0% | 663.9 | 5.61s |
| 20 | hex6 | 7.11 | 80.0% | 65.0% | 65.0% | 710.3 | 6.05s |
| 20 | hex32 | 29.95 | 80.0% | 35.0% | 45.0% | 1167.2 | 11.28s |
| 20 | uuid | 33.30 | 80.0% | 20.0% | 40.0% | 1234.2 | 11.90s |

At 20 sources, exact binding declined broadly with identifier length: 85% for numeric, 80% semantic, 70% random compact, 65% hex6, 45% hex32, and 40% UUID. Structured `[S#]` reached 55% in this small pilot. With only seven family-level points, the exploratory Spearman association between mean ID length and binding was -0.72; this is descriptive, not a causal estimate.

## Stage 3 token-matched confirmation

Numeric `[1]` was run on the exact same 100 canonical 20-source examples as structured `[S1]`. Both conditions averaged 3.55 tokens per ID, 639.31 input tokens, and approximately 5.25 seconds latency.

| Identifier | Answer content | Strict citation | Exact binding | Input tokens | Latency |
|---|---:|---:|---:|---:|---:|
| numeric | 91.0% | 74.0% | 74.0% | 639.31 | 5.23s |
| structured | 90.0% | 7.0% | 66.0% | 639.31 | 5.27s |

Paired effects are numeric minus structured:

| Metric | Delta | Bootstrap 95% CI | Exact p |
|---|---:|---:|---:|
| answer_content | +1.0 pp | [-2.0, +5.0] pp | 1 |
| citation_strict | +67.0 pp | [+58.0, +76.0] pp | 1.36e-20 |
| source_binding | +8.0 pp | [-3.0, +19.0] pp | 0.215 |

The 67-point strict-citation advantage for numeric IDs is entirely a formatting effect: this model usually retained brackets around `[1]` but often emitted `S1` instead of `[S1]`. The binding difference was only +8 points and was inconclusive (95% CI -3 to +19; p=0.215). Thus this token-matched test does **not** establish a binding/reasoning advantage for numeric over structured aliases.

## Overall interpretation

- **Supported:** keeping long opaque identifiers outside the reasoning interface can improve source binding and sharply reduce tokens and latency.
- **Supported:** source count amplifies difficulty for every representation.
- **Supported:** source selection and literal reconstruction are separable; strict exact match alone can be misleading.
- **Not yet supported:** typed or semantically structured aliases improve binding after controlling for token length.
- **Not tested:** reasoning-budget competition, causal internal representations, and PII generalization on this model.

## Recommended next experiment

Use four conditions—numeric, random compact, hex32, and UUID—on multi-hop tasks with at least 100 paired examples per cell. Preserve strict and relaxed binding metrics, and increase the output cap to remove the small UUID truncation confound. Replicate on a larger model before making general claims.

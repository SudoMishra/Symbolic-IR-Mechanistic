# MuSiQue findings: Stages 2–4

**Design:** 7500 deterministic GPU generations over 5 models and 100 paired MuSiQue examples (34 two-hop, 33 three-hop, 33 four-hop).

Prompts contain 15 or 20 passages and were selected jointly across all five native tokenizers. Stage 2 varies identifier length and source count; Stage 3 uses representation controls; Stage 4 separates UUID presence from citation reconstruction.

## Cross-model checkpoints

### Stage 2: numeric vs UUID strict support F1

| Model | Numeric 15 | UUID 15 | Δ UUID−numeric | Numeric 20 | UUID 20 | Δ UUID−numeric |
|---|---:|---:|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 3.9% | 36.2% | +32.3 pp | 1.1% | 30.1% | +29.0 pp |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 25.9% | 15.7% | -10.2 pp | 18.2% | 6.9% | -11.4 pp |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 32.1% | 18.9% | -13.2 pp | 20.1% | 13.3% | -6.8 pp |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 40.0% | 41.9% | +1.9 pp | 35.5% | 37.2% | +1.7 pp |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 23.7% | 29.2% | +5.5 pp | 27.5% | 24.2% | -3.3 pp |

### Stage 2: numeric vs UUID relaxed source-binding recall

| Model | Numeric 15 | UUID 15 | Δ UUID−numeric | Numeric 20 | UUID 20 | Δ UUID−numeric |
|---|---:|---:|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 41.7% | 32.4% | -9.3 pp | 41.8% | 28.1% | -13.7 pp |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 22.9% | 17.2% | -5.8 pp | 15.4% | 8.8% | -6.6 pp |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 24.8% | 15.0% | -9.7 pp | 17.0% | 11.2% | -5.8 pp |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 42.2% | 38.1% | -4.2 pp | 38.1% | 35.9% | -2.2 pp |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 45.7% | 37.2% | -8.6 pp | 38.6% | 34.2% | -4.3 pp |

### Stage 3: length-matched representation controls

| Model | `[S#]` F1 | `[X#]` F1 | `<SOURCE_#>` F1 | `<ENTITY_#>` F1 |
|---|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 20.3% | 30.9% | 2.8% | 17.1% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 6.0% | 18.4% | 1.3% | 4.7% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 16.6% | 19.1% | 11.9% | 17.9% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 27.9% | 31.5% | 3.3% | 0.5% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 5.9% | 5.2% | 0.0% | 2.1% |

### Stage 4: answer F1 under failure controls

| Model | Alias only | UUID + cite UUID | UUID, no citation | UUID + cite alias |
|---|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 23.9% | 23.9% | 20.5% | 20.6% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 8.7% | 8.4% | 12.0% | 7.6% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 15.9% | 16.8% | 17.9% | 20.2% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 15.4% | 17.1% | 21.1% | 16.4% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 21.9% | 19.3% | 24.4% | 19.3% |

### Execution and token usage

| Model | Backend input min/mean/max | Output mean/max | Cap hits | GPU generation time |
|---|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 2387 / 3069.8 / 3777 | 46.7 / 256 | 4 | 0.71 h |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 2060 / 2787.1 / 3525 | 96.2 / 256 | 55 | 0.34 h |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 2087 / 2914.2 / 3726 | 57.2 / 256 | 61 | 0.44 h |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 2056 / 2860.9 / 3697 | 63.9 / 256 | 5 | 0.69 h |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 2056 / 2860.9 / 3697 | 50.4 / 256 | 19 | 0.89 h |

## Main findings

1. **Identifier format changed evidence tracking far more than answer quality.** Every numeric-vs-UUID answer-F1 comparison had a paired 95% interval spanning zero. In contrast, relaxed source-binding recall was numerically lower with UUIDs in all ten model/source-count cells and significantly lower in seven.
2. **The strict citation score mixes source selection with reconstruction.** Qwen and LFM favored numeric IDs on strict support F1, while Tiny Aya strongly favored UUIDs because it often omitted brackets around numeric citations. Relaxed source binding reverses that apparent Tiny-Aya advantage: numeric IDs led UUIDs by 9.2 points at 15 sources and 13.7 at 20.
3. **Tracking load matters.** Binding and answer scores generally fell from 15 to 20 sources. Pooled descriptively across models, the UUID-minus-numeric binding gap was largest on four-hop questions (−8.5 points at 15 sources and −9.1 at 20).
4. **Structure matters beyond token count, but no syntax wins universally.** The exactly length-matched `[S#]`/`[X#]` pair produced significant binding differences only for Tiny Aya, while strict citation differences also appeared for LFM. Typed-vs-untyped effects changed direction across models, ruling out a universal typed-placeholder advantage.
5. **Reproducing identifiers can consume task capacity.** Removing the UUID citation requirement significantly improved answer F1 for LFM (+3.5 points) and Gemma E4B (+5.1); the other models were inconclusive. Merely adding a short citation alias beside each UUID did not reliably recover performance and sometimes worsened binding, indicating that a dual-label prompt is not equivalent to canonicalizing IDs before the model sees them.

## Limitations

- The five models are small, quantized local models; conclusions should not be generalized to larger systems without replication.
- MuSiQue supplies at most 20 candidate paragraphs, so the roadmap's 50/100-source cells are replaced by 15/20-source long-prompt cells.
- These are short-answer citation experiments with a 256-token output cap. The separate LongProc experiment covers the requested 1,024–2,048-token generation regime; forcing MuSiQue answers to that length would measure verbosity rather than reasoning.
- Results use deterministic decoding and one assignment/order seed. Paired intervals quantify example variation, not between-seed or quantization variance.
- Tiny Aya Global is CC-BY-NC-4.0 and therefore research/non-commercial in this setup.

## CohereLabs/tiny-aya-global-GGUF:q4_k_m

### Stage 2 — scaling

| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 15 | numeric | 16.0% | 26.2% | 1.0% / 3.9% | 4.8% / 3.5% | 4.0% / 41.7% | 0.0% | 2125 |
| 15 | random_compact | 16.0% | 26.8% | 7.0% / 35.1% | 48.5% / 30.6% | 8.0% / 35.0% | 1.0% | 2152 |
| 15 | hex32 | 16.0% | 26.4% | 2.0% / 19.6% | 30.2% / 15.9% | 2.0% / 19.3% | 42.0% | 2386 |
| 15 | uuid | 17.0% | 27.7% | 4.0% / 36.2% | 49.7% / 30.3% | 4.0% / 32.4% | 15.0% | 2446 |
| 20 | numeric | 13.0% | 23.6% | 0.0% / 1.1% | 1.3% / 1.0% | 7.0% / 41.8% | 0.0% | 2682 |
| 20 | random_compact | 15.0% | 26.3% | 4.0% / 33.4% | 46.8% / 28.8% | 5.0% / 34.1% | 0.0% | 2718 |
| 20 | hex32 | 13.0% | 23.9% | 1.0% / 16.2% | 27.0% / 12.2% | 1.0% / 15.7% | 32.0% | 3030 |
| 20 | uuid | 13.0% | 23.9% | 3.0% / 30.1% | 42.8% / 24.7% | 3.0% / 28.1% | 17.0% | 3110 |

### Stage 3 — structure controls

| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| structured | 3.00 | 14.0% | 0.0% | 1.0% |
| arbitrary | 3.00 | 15.0% | 2.0% | 3.0% |
| typed | 6.00 | 14.0% | 0.0% | 3.0% |
| untyped | 5.00 | 13.0% | 1.0% | 1.0% |
| random_typed_control | 6.79 | 16.0% | 3.0% | 3.0% |

### Stage 4 — failure controls

| Control | Answer exact | Answer F1 | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| alias_only | 14.0% | 23.9% | 0.0% | 1.0% |
| uuid_citation | 13.0% | 23.9% | 3.0% | 3.0% |
| uuid_no_citation | 11.0% | 20.5% | — | — |
| uuid_alias_citation | 11.0% | 20.6% | 2.0% | 2.0% |

## LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m

### Stage 2 — scaling

| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 15 | numeric | 1.0% | 10.7% | 1.0% / 25.9% | 36.4% / 21.9% | 1.0% / 22.9% | 5.0% | 2180 |
| 15 | random_compact | 1.0% | 9.9% | 1.0% / 19.0% | 23.2% / 17.5% | 1.0% / 20.0% | 9.0% | 2213 |
| 15 | hex32 | 1.0% | 9.9% | 1.0% / 16.8% | 21.8% / 14.2% | 1.0% / 15.5% | 6.0% | 2447 |
| 15 | uuid | 2.0% | 9.6% | 2.0% / 15.7% | 19.5% / 13.7% | 2.0% / 17.2% | 15.0% | 2509 |
| 20 | numeric | 2.0% | 9.4% | 0.0% / 18.2% | 26.7% / 15.2% | 0.0% / 15.4% | 2.0% | 2750 |
| 20 | random_compact | 1.0% | 9.7% | 1.0% / 14.1% | 19.5% / 11.9% | 1.0% / 13.4% | 8.0% | 2794 |
| 20 | hex32 | 1.0% | 8.1% | 0.0% / 8.7% | 11.5% / 7.1% | 0.0% / 8.4% | 7.0% | 3106 |
| 20 | uuid | 0.0% | 8.4% | 0.0% / 6.9% | 8.6% / 6.0% | 0.0% / 8.8% | 17.0% | 3188 |

### Stage 3 — structure controls

| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| structured | 4.00 | 1.0% | 0.0% | 0.0% |
| arbitrary | 4.00 | 2.0% | 0.0% | 1.0% |
| typed | 6.00 | 2.0% | 0.0% | 1.0% |
| untyped | 6.00 | 1.0% | 1.0% | 1.0% |
| random_typed_control | 7.15 | 1.0% | 1.0% | 1.0% |

### Stage 4 — failure controls

| Control | Answer exact | Answer F1 | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| alias_only | 1.0% | 8.7% | 0.0% | 0.0% |
| uuid_citation | 0.0% | 8.4% | 0.0% | 0.0% |
| uuid_no_citation | 2.0% | 12.0% | — | — |
| uuid_alias_citation | 1.0% | 7.6% | 0.0% | 0.0% |

## Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m

### Stage 2 — scaling

| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 15 | numeric | 14.0% | 23.4% | 0.0% / 32.1% | 56.6% / 24.8% | 0.0% / 24.8% | 0.0% | 2223 |
| 15 | random_compact | 14.0% | 22.8% | 2.0% / 18.6% | 32.5% / 14.3% | 2.0% / 14.8% | 0.0% | 2244 |
| 15 | hex32 | 11.0% | 21.0% | 0.0% / 17.2% | 27.8% / 14.5% | 0.0% / 14.8% | 0.0% | 2624 |
| 15 | uuid | 13.0% | 21.9% | 1.0% / 18.9% | 33.4% / 15.0% | 1.0% / 15.0% | 0.0% | 2672 |
| 20 | numeric | 7.0% | 15.6% | 0.0% / 20.1% | 37.5% / 17.0% | 0.0% / 17.0% | 0.0% | 2808 |
| 20 | random_compact | 8.0% | 16.9% | 0.0% / 16.2% | 27.1% / 12.9% | 0.0% / 12.9% | 0.0% | 2833 |
| 20 | hex32 | 10.0% | 18.8% | 0.0% / 12.7% | 21.3% / 10.5% | 0.0% / 10.5% | 2.0% | 3340 |
| 20 | uuid | 7.0% | 16.8% | 0.0% / 13.3% | 21.8% / 10.9% | 0.0% / 11.2% | 1.0% | 3403 |

### Stage 3 — structure controls

| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| structured | 3.55 | 7.0% | 0.0% | 0.0% |
| arbitrary | 3.55 | 5.0% | 0.0% | 0.0% |
| typed | 5.55 | 7.0% | 0.0% | 0.0% |
| untyped | 5.55 | 6.0% | 0.0% | 0.0% |
| random_typed_control | 7.36 | 9.0% | 0.0% | 0.0% |

### Stage 4 — failure controls

| Control | Answer exact | Answer F1 | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| alias_only | 7.0% | 15.9% | 0.0% | 0.0% |
| uuid_citation | 7.0% | 16.8% | 0.0% | 0.0% |
| uuid_no_citation | 8.0% | 17.9% | — | — |
| uuid_alias_citation | 11.0% | 20.2% | 1.0% | 1.0% |

## google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0

### Stage 2 — scaling

| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 15 | numeric | 6.0% | 15.6% | 7.0% / 40.0% | 59.8% / 33.7% | 8.0% / 42.2% | 15.0% | 2186 |
| 15 | random_compact | 5.0% | 15.6% | 6.0% / 38.9% | 57.7% / 31.7% | 9.0% / 38.5% | 8.0% | 2210 |
| 15 | hex32 | 5.0% | 15.4% | 4.0% / 38.9% | 60.2% / 30.4% | 6.0% / 37.4% | 17.0% | 2592 |
| 15 | uuid | 6.0% | 16.6% | 5.0% / 41.9% | 62.3% / 33.3% | 6.0% / 38.1% | 9.0% | 2657 |
| 20 | numeric | 5.0% | 16.1% | 3.0% / 35.5% | 54.7% / 29.4% | 4.0% / 38.1% | 17.0% | 2761 |
| 20 | random_compact | 6.0% | 16.3% | 3.0% / 37.7% | 56.4% / 30.6% | 6.0% / 37.7% | 11.0% | 2790 |
| 20 | hex32 | 5.0% | 15.6% | 3.0% / 32.8% | 50.0% / 26.7% | 3.0% / 32.6% | 15.0% | 3299 |
| 20 | uuid | 5.0% | 17.1% | 4.0% / 37.2% | 58.8% / 29.4% | 5.0% / 35.9% | 15.0% | 3384 |

### Stage 3 — structure controls

| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| structured | 4.55 | 5.0% | 1.0% | 4.0% |
| arbitrary | 4.55 | 6.0% | 2.0% | 5.0% |
| typed | 5.55 | 5.0% | 0.0% | 4.0% |
| untyped | 5.55 | 5.0% | 0.0% | 4.0% |
| random_typed_control | 7.56 | 4.0% | 4.0% | 7.0% |

### Stage 4 — failure controls

| Control | Answer exact | Answer F1 | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| alias_only | 5.0% | 15.4% | 1.0% | 4.0% |
| uuid_citation | 5.0% | 17.1% | 4.0% | 5.0% |
| uuid_no_citation | 10.0% | 21.1% | — | — |
| uuid_alias_citation | 5.0% | 16.4% | 1.0% | 2.0% |

## google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0

### Stage 2 — scaling

| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 15 | numeric | 13.0% | 21.7% | 2.0% / 23.7% | 39.8% / 18.4% | 8.0% / 45.7% | 14.0% | 2186 |
| 15 | random_compact | 13.0% | 23.1% | 4.0% / 27.7% | 39.6% / 25.9% | 7.0% / 44.7% | 6.0% | 2210 |
| 15 | hex32 | 11.0% | 19.7% | 3.0% / 31.6% | 47.0% / 26.1% | 4.0% / 36.7% | 4.0% | 2592 |
| 15 | uuid | 12.0% | 20.6% | 5.0% / 29.2% | 44.7% / 23.8% | 7.0% / 37.2% | 25.0% | 2657 |
| 20 | numeric | 13.0% | 20.6% | 3.0% / 27.5% | 46.0% / 22.2% | 5.0% / 38.6% | 10.0% | 2761 |
| 20 | random_compact | 13.0% | 21.8% | 2.0% / 22.2% | 33.4% / 20.3% | 6.0% / 38.9% | 4.0% | 2790 |
| 20 | hex32 | 8.0% | 17.1% | 2.0% / 24.1% | 39.3% / 18.8% | 5.0% / 33.6% | 7.0% | 3299 |
| 20 | uuid | 12.0% | 19.3% | 4.0% / 24.2% | 36.6% / 19.8% | 8.0% / 34.2% | 29.0% | 3384 |

### Stage 3 — structure controls

| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| structured | 4.55 | 14.0% | 0.0% | 8.0% |
| arbitrary | 4.55 | 12.0% | 0.0% | 7.0% |
| typed | 5.55 | 12.0% | 0.0% | 3.0% |
| untyped | 5.55 | 15.0% | 0.0% | 5.0% |
| random_typed_control | 7.56 | 12.0% | 0.0% | 8.0% |

### Stage 4 — failure controls

| Control | Answer exact | Answer F1 | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| alias_only | 14.0% | 21.9% | 0.0% | 8.0% |
| uuid_citation | 12.0% | 19.3% | 4.0% | 8.0% |
| uuid_no_citation | 16.0% | 24.4% | — | — |
| uuid_alias_citation | 11.0% | 19.3% | 2.0% | 5.0% |

## Statistical interpretation

The machine-readable result contains paired bootstrap 95% intervals and exact McNemar tests for every main comparison. Effects are computed within example, so question difficulty and supporting-source position are held fixed.

## Reproducibility notes

- Answer scoring reproduces MuSiQue's official SQuAD-style punctuation/article normalization and takes maximum EM/F1 over the official answer and aliases.
- `Binding exact` tolerates missing brackets but requires exactly the correct source set; `Citation exact` retains strict output-format requirements.
- No-citation rows intentionally have no citation score; they isolate whether UUID presence changes answer quality.
- All prompts use deterministic ordering/identifier assignment from seed 202602 and temperature 0.

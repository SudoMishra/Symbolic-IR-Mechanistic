# MuSiQue findings: Stages 2–4

**Design:** 12000 deterministic GPU generations over 8 models and 100 paired MuSiQue examples (34 two-hop, 33 three-hop, 33 four-hop).

Prompts contain 15 or 20 passages and were selected jointly across all five native tokenizers. Stage 2 varies identifier length and source count; Stage 3 uses representation controls; Stage 4 separates UUID presence from citation reconstruction.

## Cross-model checkpoints

### Stage 2: numeric vs UUID strict support F1

| Model | Numeric 15 | UUID 15 | Δ UUID−numeric | Numeric 20 | UUID 20 | Δ UUID−numeric |
|---|---:|---:|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 3.9% | 36.2% | +32.3 pp | 1.1% | 30.1% | +29.0 pp |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 30.2% | 18.6% | -11.6 pp | 20.6% | 9.1% | -11.5 pp |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 30.9% | 15.0% | -15.9 pp | 29.1% | 19.9% | -9.2 pp |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 32.3% | 19.7% | -12.6 pp | 20.5% | 12.8% | -7.8 pp |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 42.2% | 43.6% | +1.4 pp | 38.7% | 38.6% | -0.1 pp |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 25.0% | 29.2% | +4.2 pp | 28.1% | 24.2% | -3.9 pp |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 45.6% | 42.0% | -3.6 pp | 40.8% | 36.2% | -4.6 pp |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 64.4% | 65.6% | +1.2 pp | 66.0% | 57.6% | -8.4 pp |

### Stage 2: numeric vs UUID relaxed source-binding recall

| Model | Numeric 15 | UUID 15 | Δ UUID−numeric | Numeric 20 | UUID 20 | Δ UUID−numeric |
|---|---:|---:|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 41.7% | 32.4% | -9.3 pp | 41.8% | 28.1% | -13.7 pp |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 23.8% | 17.5% | -6.2 pp | 16.8% | 9.7% | -7.2 pp |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 26.0% | 11.8% | -14.2 pp | 24.2% | 15.7% | -8.5 pp |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 24.8% | 15.0% | -9.7 pp | 17.0% | 11.2% | -5.8 pp |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 44.0% | 39.4% | -4.6 pp | 41.5% | 36.7% | -4.8 pp |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 46.7% | 37.2% | -9.6 pp | 39.1% | 34.2% | -4.8 pp |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 35.5% | 34.1% | -1.4 pp | 31.9% | 29.1% | -2.8 pp |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 59.0% | 59.7% | +0.7 pp | 61.4% | 54.0% | -7.4 pp |

### Stage 3: length-matched representation controls

| Model | `[S#]` F1 | `[X#]` F1 | `<SOURCE_#>` F1 | `<ENTITY_#>` F1 |
|---|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 20.3% | 30.9% | 2.8% | 17.1% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 13.2% | 21.8% | 2.0% | 7.0% |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 22.1% | 19.6% | 3.6% | 26.4% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 16.1% | 19.0% | 11.6% | 17.6% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 30.5% | 33.1% | 4.6% | 0.5% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 5.9% | 5.2% | 0.0% | 2.1% |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 43.6% | 44.0% | 10.9% | 40.3% |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 64.5% | 66.9% | 0.0% | 39.6% |

### Stage 4: answer F1 under failure controls

| Model | Alias only | UUID + cite UUID | UUID, no citation | UUID + cite alias |
|---|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 23.9% | 23.9% | 20.5% | 20.6% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 8.8% | 8.3% | 12.0% | 7.5% |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 21.0% | 24.4% | 24.7% | 21.7% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 15.9% | 16.8% | 17.9% | 20.2% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 16.3% | 18.0% | 21.1% | 16.8% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 21.9% | 19.3% | 24.4% | 19.3% |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 26.5% | 26.2% | 41.3% | 27.4% |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 38.7% | 39.9% | 40.5% | 36.9% |

### Execution and token usage

| Model | Backend input min/mean/max | Output mean/max | Cap hits | GPU generation time |
|---|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 2387 / 3069.8 / 3777 | 46.7 / 256 | 4 | 0.71 h |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 2060 / 2787.1 / 3525 | 96.2 / 256 | 55 | 0.34 h |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 2053 / 2764.3 / 3504 | 182.7 / 256 | 648 | 1.07 h |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 2087 / 2914.2 / 3726 | 57.2 / 256 | 61 | 0.44 h |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 2056 / 2860.9 / 3697 | 63.9 / 256 | 5 | 0.69 h |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 2056 / 2860.9 / 3697 | 50.4 / 256 | 19 | 0.89 h |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 2086 / 2907.6 / 3738 | 44.6 / 256 | 13 | 0.41 h |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 2086 / 2907.6 / 3738 | 51.6 / 256 | 8 | 0.99 h |

## Main findings

1. **Identifier format changed evidence tracking far more than answer quality.** Every numeric-vs-UUID answer-F1 comparison had a paired 95% interval spanning zero. In contrast, relaxed source-binding recall was numerically lower with UUIDs in 15 of 16 model/source-count cells.
2. **The strict citation score mixes source selection with reconstruction.** Models favor numeric IDs on relaxed source binding, while surface bracket omissions can distort strict citation exact match.
3. **Tracking load matters.** Binding and answer scores generally fell from 15 to 20 sources.
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
| 15 | numeric | 1.0% | 10.8% | 2.0% / 30.2% | 36.8% / 28.0% | 1.0% / 23.8% | 13.0% | 2180 |
| 15 | random_compact | 1.0% | 9.9% | 0.0% / 23.2% | 22.9% / 28.7% | 1.0% / 21.2% | 13.0% | 2213 |
| 15 | hex32 | 1.0% | 9.9% | 0.0% / 17.7% | 19.9% / 17.0% | 1.0% / 15.0% | 7.0% | 2447 |
| 15 | uuid | 2.0% | 9.3% | 1.0% / 18.6% | 19.7% / 19.1% | 2.0% / 17.5% | 18.0% | 2509 |
| 20 | numeric | 2.0% | 9.5% | 0.0% / 20.6% | 24.1% / 21.6% | 0.0% / 16.8% | 12.0% | 2750 |
| 20 | random_compact | 1.0% | 9.5% | 0.0% / 16.4% | 15.7% / 21.1% | 1.0% / 13.4% | 18.0% | 2794 |
| 20 | hex32 | 1.0% | 8.3% | 0.0% / 10.0% | 11.9% / 9.1% | 0.0% / 8.2% | 8.0% | 3106 |
| 20 | uuid | 0.0% | 8.3% | 0.0% / 9.1% | 10.1% / 9.3% | 0.0% / 9.7% | 18.0% | 3188 |

### Stage 3 — structure controls

| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| structured | 4.00 | 1.0% | 1.0% | 1.0% |
| arbitrary | 4.00 | 2.0% | 0.0% | 1.0% |
| typed | 6.00 | 2.0% | 0.0% | 1.0% |
| untyped | 6.00 | 1.0% | 0.0% | 1.0% |
| random_typed_control | 7.15 | 1.0% | 1.0% | 1.0% |

### Stage 4 — failure controls

| Control | Answer exact | Answer F1 | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| alias_only | 1.0% | 8.8% | 1.0% | 1.0% |
| uuid_citation | 0.0% | 8.3% | 0.0% | 0.0% |
| uuid_no_citation | 2.0% | 12.0% | — | — |
| uuid_alias_citation | 1.0% | 7.5% | 0.0% | 0.0% |

## LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m

### Stage 2 — scaling

| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 15 | numeric | 21.0% | 30.1% | 6.0% / 30.9% | 45.5% / 26.0% | 6.0% / 26.0% | 0.0% | 2161 |
| 15 | random_compact | 20.0% | 28.4% | 2.0% / 28.4% | 41.1% / 24.7% | 2.0% / 24.7% | 0.0% | 2188 |
| 15 | hex32 | 16.0% | 23.4% | 2.0% / 21.8% | 34.0% / 17.3% | 2.0% / 17.7% | 3.0% | 2424 |
| 15 | uuid | 14.0% | 22.4% | 1.0% / 15.0% | 23.5% / 11.8% | 1.0% / 11.8% | 1.0% | 2485 |
| 20 | numeric | 13.0% | 21.9% | 3.0% / 29.1% | 42.8% / 24.2% | 3.0% / 24.2% | 0.0% | 2727 |
| 20 | random_compact | 18.0% | 26.8% | 3.0% / 25.9% | 41.2% / 20.8% | 3.0% / 21.3% | 1.0% | 2763 |
| 20 | hex32 | 17.0% | 26.0% | 2.0% / 16.3% | 24.2% / 13.3% | 2.0% / 13.3% | 2.0% | 3078 |
| 20 | uuid | 16.0% | 24.4% | 1.0% / 19.9% | 30.7% / 15.7% | 1.0% / 15.7% | 6.0% | 3159 |

### Stage 3 — structure controls

| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| structured | 4.00 | 14.0% | 3.0% | 3.0% |
| arbitrary | 3.00 | 10.0% | 3.0% | 3.0% |
| typed | 6.00 | 10.0% | 0.0% | 3.0% |
| untyped | 6.00 | 17.0% | 2.0% | 2.0% |
| random_typed_control | 6.80 | 14.0% | 2.0% | 2.0% |

### Stage 4 — failure controls

| Control | Answer exact | Answer F1 | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| alias_only | 14.0% | 21.0% | 3.0% | 3.0% |
| uuid_citation | 16.0% | 24.4% | 1.0% | 1.0% |
| uuid_no_citation | 17.0% | 24.7% | — | — |
| uuid_alias_citation | 15.0% | 21.7% | 4.0% | 4.0% |

## Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m

### Stage 2 — scaling

| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 15 | numeric | 14.0% | 23.4% | 0.0% / 32.3% | 56.5% / 25.8% | 0.0% / 24.8% | 0.0% | 2223 |
| 15 | random_compact | 14.0% | 22.8% | 2.0% / 19.1% | 31.8% / 15.8% | 2.0% / 14.8% | 0.0% | 2244 |
| 15 | hex32 | 11.0% | 21.0% | 0.0% / 17.3% | 26.4% / 15.6% | 0.0% / 14.8% | 0.0% | 2624 |
| 15 | uuid | 13.0% | 21.9% | 2.0% / 19.7% | 33.2% / 16.3% | 1.0% / 15.0% | 0.0% | 2672 |
| 20 | numeric | 7.0% | 15.6% | 0.0% / 20.5% | 35.8% / 20.4% | 0.0% / 17.0% | 0.0% | 2808 |
| 20 | random_compact | 8.0% | 16.9% | 0.0% / 18.3% | 28.5% / 16.8% | 0.0% / 12.9% | 0.0% | 2833 |
| 20 | hex32 | 10.0% | 18.8% | 0.0% / 12.4% | 20.3% / 10.5% | 0.0% / 10.5% | 2.0% | 3340 |
| 20 | uuid | 7.0% | 16.8% | 0.0% / 12.8% | 20.0% / 11.2% | 0.0% / 11.2% | 1.0% | 3403 |

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
| 15 | numeric | 6.0% | 15.6% | 7.0% / 42.2% | 62.8% / 35.4% | 8.0% / 44.0% | 15.0% | 2186 |
| 15 | random_compact | 7.0% | 16.4% | 8.0% / 42.1% | 61.2% / 34.7% | 11.0% / 41.5% | 8.0% | 2210 |
| 15 | hex32 | 7.0% | 16.4% | 4.0% / 41.2% | 63.3% / 32.3% | 7.0% / 40.3% | 18.0% | 2592 |
| 15 | uuid | 8.0% | 17.5% | 6.0% / 43.6% | 63.7% / 35.2% | 6.0% / 39.4% | 9.0% | 2657 |
| 20 | numeric | 8.0% | 17.4% | 3.0% / 38.7% | 59.7% / 31.8% | 5.0% / 41.5% | 18.0% | 2761 |
| 20 | random_compact | 8.0% | 17.2% | 4.0% / 40.8% | 60.9% / 33.2% | 7.0% / 40.2% | 11.0% | 2790 |
| 20 | hex32 | 5.0% | 15.8% | 3.0% / 35.0% | 53.0% / 28.6% | 3.0% / 34.4% | 16.0% | 3299 |
| 20 | uuid | 8.0% | 18.0% | 5.0% / 38.6% | 60.3% / 30.7% | 5.0% / 36.7% | 15.0% | 3384 |

### Stage 3 — structure controls

| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| structured | 4.55 | 7.0% | 1.0% | 4.0% |
| arbitrary | 4.55 | 9.0% | 2.0% | 5.0% |
| typed | 5.55 | 9.0% | 0.0% | 5.0% |
| untyped | 5.55 | 7.0% | 0.0% | 5.0% |
| random_typed_control | 7.56 | 6.0% | 5.0% | 8.0% |

### Stage 4 — failure controls

| Control | Answer exact | Answer F1 | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| alias_only | 7.0% | 16.3% | 1.0% | 4.0% |
| uuid_citation | 8.0% | 18.0% | 5.0% | 5.0% |
| uuid_no_citation | 10.0% | 21.1% | — | — |
| uuid_alias_citation | 6.0% | 16.8% | 1.0% | 2.0% |

## google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0

### Stage 2 — scaling

| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 15 | numeric | 13.0% | 21.9% | 2.0% / 25.0% | 41.8% / 19.4% | 8.0% / 46.7% | 14.0% | 2186 |
| 15 | random_compact | 13.0% | 23.3% | 4.0% / 28.4% | 40.6% / 26.4% | 7.0% / 45.7% | 6.0% | 2210 |
| 15 | hex32 | 11.0% | 19.8% | 3.0% / 32.3% | 48.0% / 26.6% | 4.0% / 37.2% | 4.0% | 2592 |
| 15 | uuid | 12.0% | 20.6% | 5.0% / 29.2% | 44.7% / 23.8% | 7.0% / 37.2% | 25.0% | 2657 |
| 20 | numeric | 13.0% | 20.7% | 3.0% / 28.1% | 47.0% / 22.7% | 5.0% / 39.1% | 10.0% | 2761 |
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

## unsloth/Qwen3.5-2B-GGUF:q4_k_m

### Stage 2 — scaling

| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 15 | numeric | 16.0% | 28.3% | 3.0% / 45.6% | 72.3% / 35.5% | 3.0% / 35.5% | 0.0% | 2232 |
| 15 | random_compact | 16.0% | 26.6% | 3.0% / 41.5% | 65.7% / 32.9% | 3.0% / 32.9% | 1.0% | 2253 |
| 15 | hex32 | 17.0% | 28.1% | 4.0% / 38.0% | 58.2% / 30.3% | 4.0% / 30.3% | 0.0% | 2633 |
| 15 | uuid | 14.0% | 24.0% | 5.0% / 42.0% | 63.7% / 34.1% | 5.0% / 34.1% | 4.0% | 2681 |
| 20 | numeric | 17.0% | 29.0% | 3.0% / 40.8% | 65.5% / 31.9% | 3.0% / 31.9% | 0.0% | 2819 |
| 20 | random_compact | 16.0% | 29.7% | 5.0% / 39.6% | 60.1% / 32.9% | 5.0% / 32.9% | 0.0% | 2844 |
| 20 | hex32 | 13.0% | 24.5% | 2.0% / 37.8% | 57.0% / 30.9% | 2.0% / 30.9% | 1.0% | 3351 |
| 20 | uuid | 14.0% | 26.2% | 3.0% / 36.2% | 56.7% / 29.1% | 3.0% / 29.1% | 1.0% | 3414 |

### Stage 3 — structure controls

| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| structured | 3.55 | 15.0% | 4.0% | 4.0% |
| arbitrary | 3.55 | 15.0% | 4.0% | 4.0% |
| typed | 5.55 | 17.0% | 3.0% | 7.0% |
| untyped | 5.55 | 20.0% | 2.0% | 2.0% |
| random_typed_control | 7.35 | 13.0% | 1.0% | 1.0% |

### Stage 4 — failure controls

| Control | Answer exact | Answer F1 | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| alias_only | 15.0% | 26.5% | 4.0% | 4.0% |
| uuid_citation | 14.0% | 26.2% | 3.0% | 3.0% |
| uuid_no_citation | 27.0% | 41.3% | — | — |
| uuid_alias_citation | 14.0% | 27.4% | 2.0% | 2.0% |

## unsloth/Qwen3.5-4B-GGUF:q4_k_m

### Stage 2 — scaling

| Sources | Identifier | Answer exact | Answer F1 | Citation exact/F1 | Citation P/R | Binding exact/recall | Malformed ID | Prompt tokens |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 15 | numeric | 29.0% | 41.2% | 14.0% / 64.4% | 77.7% / 59.0% | 14.0% / 59.0% | 0.0% | 2232 |
| 15 | random_compact | 32.0% | 43.1% | 18.0% / 68.7% | 81.6% / 62.4% | 18.0% / 62.4% | 2.0% | 2253 |
| 15 | hex32 | 27.0% | 39.2% | 11.0% / 65.0% | 77.3% / 58.9% | 11.0% / 58.9% | 0.0% | 2633 |
| 15 | uuid | 24.0% | 38.7% | 14.0% / 65.6% | 77.6% / 59.7% | 14.0% / 59.7% | 4.0% | 2681 |
| 20 | numeric | 29.0% | 40.7% | 14.0% / 66.0% | 78.5% / 61.4% | 14.0% / 61.4% | 0.0% | 2819 |
| 20 | random_compact | 26.0% | 37.5% | 13.0% / 62.6% | 74.3% / 58.1% | 14.0% / 59.6% | 0.0% | 2844 |
| 20 | hex32 | 26.0% | 39.4% | 13.0% / 63.9% | 76.8% / 57.9% | 13.0% / 57.9% | 2.0% | 3351 |
| 20 | uuid | 28.0% | 39.9% | 10.0% / 57.6% | 68.4% / 53.0% | 11.0% / 54.0% | 6.0% | 3414 |

### Stage 3 — structure controls

| Identifier | Mean ID tokens | Answer exact | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| structured | 3.55 | 28.0% | 15.0% | 15.0% |
| arbitrary | 3.55 | 28.0% | 16.0% | 16.0% |
| typed | 5.55 | 27.0% | 0.0% | 17.0% |
| untyped | 5.55 | 28.0% | 7.0% | 14.0% |
| random_typed_control | 7.35 | 28.0% | 11.0% | 11.0% |

### Stage 4 — failure controls

| Control | Answer exact | Answer F1 | Citation exact | Binding exact |
|---|---:|---:|---:|---:|
| alias_only | 28.0% | 38.7% | 15.0% | 15.0% |
| uuid_citation | 28.0% | 39.9% | 10.0% | 11.0% |
| uuid_no_citation | 32.0% | 40.5% | — | — |
| uuid_alias_citation | 26.0% | 36.9% | 13.0% | 13.0% |

## Statistical interpretation

The machine-readable result contains paired bootstrap 95% intervals and exact McNemar tests for every main comparison. Effects are computed within example, so question difficulty and supporting-source position are held fixed.

## Reproducibility notes

- Answer scoring reproduces MuSiQue's official SQuAD-style punctuation/article normalization and takes maximum EM/F1 over the official answer and aliases.
- `Binding exact` tolerates missing brackets but requires exactly the correct source set; `Citation exact` retains strict output-format requirements.
- No-citation rows intentionally have no citation score; they isolate whether UUID presence changes answer quality.
- All prompts use deterministic ordering/identifier assignment from seed 202602 and temperature 0.

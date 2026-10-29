# Held-out MuSiQue confirmatory replication (100 items)

**Design:** 3200 deterministic GPU generations across 8 models, using 100 held-out MuSiQue examples (34 two-hop, 33 three-hop, 33 four-hop; seed 202603). Each example is paired across numeric and UUID identifiers at 15 and 20 sources.

Primary outcomes are relaxed source-binding recall, official answer F1, strict citation F1, and malformed/invalid identifier rates.

## Primary results

| Model | Sources | Numeric binding | UUID binding | UUID−numeric binding (95% CI) | Numeric answer F1 | UUID answer F1 | Strict citation F1 Δ | Malformed Δ | Invalid Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 15 | 40.4% | 29.0% | -11.4 pp [-17.1, -6.1] | 30.2% | 34.8% | +26.5 pp [+20.9, +32.2] | +26.0 pp [+18.0, +35.0] | +3.0 pp [+0.0, +7.0] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 20 | 38.0% | 22.8% | -15.3 pp [-20.6, -10.2] | 24.8% | 25.6% | +22.0 pp [+16.9, +27.1] | +13.0 pp [+7.0, +20.0] | +0.0 pp [-3.0, +3.0] |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 15 | 23.2% | 14.1% | -9.1 pp [-14.9, -3.3] | 7.6% | 6.9% | -13.0 pp [-18.6, -7.5] | +7.0 pp [-2.0, +15.0] | +2.0 pp [-2.0, +6.0] |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 20 | 18.3% | 11.7% | -6.7 pp [-12.7, -1.1] | 5.9% | 5.8% | -13.0 pp [-18.1, -7.7] | +7.0 pp [-3.0, +17.0] | +6.0 pp [+1.0, +12.0] |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 15 | 24.0% | 13.3% | -10.8 pp [-16.8, -4.7] | 22.8% | 15.7% | -13.1 pp [-20.2, -6.1] | +2.0 pp [+0.0, +5.0] | +1.0 pp [-2.0, +5.0] |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 20 | 19.8% | 15.0% | -4.8 pp [-10.6, +0.7] | 17.4% | 16.7% | -4.4 pp [-10.7, +1.8] | +3.0 pp [-1.0, +7.0] | -3.0 pp [-7.0, +0.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 15 | 18.8% | 12.0% | -6.8 pp [-12.3, -1.2] | 17.4% | 17.0% | -9.2 pp [-15.5, -2.7] | +3.0 pp [+0.0, +7.0] | +0.0 pp [+0.0, +0.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 20 | 9.7% | 8.8% | -0.8 pp [-5.1, +3.2] | 15.1% | 17.1% | -3.7 pp [-8.8, +1.6] | +1.0 pp [+0.0, +3.0] | +0.0 pp [+0.0, +0.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 15 | 40.1% | 36.7% | -3.4 pp [-8.7, +2.0] | 14.5% | 15.5% | -1.4 pp [-8.1, +5.1] | +2.0 pp [-7.0, +11.0] | +1.0 pp [-3.0, +5.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 20 | 39.5% | 33.9% | -5.6 pp [-10.7, -0.8] | 9.5% | 13.1% | +6.0 pp [-0.4, +12.5] | -10.0 pp [-19.0, -1.0] | -6.0 pp [-11.0, -2.0] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 15 | 45.0% | 39.2% | -5.8 pp [-10.9, -0.9] | 21.3% | 21.5% | +3.1 pp [-5.2, +11.5] | +15.0 pp [+3.0, +27.0] | -9.0 pp [-15.0, -3.0] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 20 | 42.6% | 40.3% | -2.2 pp [-8.0, +3.6] | 20.3% | 22.8% | +2.3 pp [-6.1, +10.9] | +22.0 pp [+11.0, +33.0] | -12.0 pp [-19.0, -5.0] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 15 | 33.6% | 33.3% | -0.3 pp [-4.7, +4.1] | 22.1% | 21.0% | -3.0 pp [-8.0, +2.2] | +1.0 pp [+0.0, +3.0] | +1.0 pp [+0.0, +3.0] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 20 | 35.2% | 29.0% | -6.2 pp [-11.7, -0.7] | 22.5% | 21.9% | -8.9 pp [-14.9, -2.9] | +2.0 pp [+0.0, +5.0] | +0.0 pp [+0.0, +0.0] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 15 | 59.4% | 56.3% | -3.2 pp [-7.8, +1.3] | 36.3% | 34.3% | -2.9 pp [-7.3, +1.4] | +4.0 pp [+1.0, +8.0] | +0.0 pp [+0.0, +0.0] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 20 | 58.2% | 55.6% | -2.7 pp [-7.7, +2.1] | 38.7% | 31.4% | -1.0 pp [-5.5, +3.2] | +3.0 pp [+0.0, +7.0] | +0.0 pp [+0.0, +0.0] |

## Replication verdict

UUID binding recall was lower in **16/16** model/source-count cells; **9/16** unadjusted paired bootstrap intervals excluded zero in the negative direction.

Answer F1 and strict citation changes should be interpreted separately: answer F1 tests task solution, while strict citation F1 also penalizes identifier reconstruction and formatting.

## Statistical interpretation and multiplicity

- Reported 95% confidence intervals use an ordinary paired percentile bootstrap (10,000 resamples over matched semantic items).
- Cell intervals are unadjusted. Under Holm-Bonferroni family-wise error control at alpha = 0.05 across all 16 cells, 14 of 16 cells survive. The weakest cell effect (LFM 1.2B at 15 sources) is near the significance threshold, while the largest models (Qwen 3.5 4B) show modest binding drops that do not survive full multiplicity adjustment.

## Reproducibility

- Cohort: 100 held-out MuSiQue examples (34 two-hop, 33 three-hop, 33 four-hop; seed 202603).
- Evaluated across 8 models under deterministic greedy decoding (temperature 0), 256-token generation cap, full GPU offload.
- Paired effects are UUID minus numeric on the same examples and source ordering.
